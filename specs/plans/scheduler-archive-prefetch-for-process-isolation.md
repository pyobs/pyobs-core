# Plan: Split archive prefetch from CPU-bound merit evaluation, to unblock a `ProcessPoolExecutor`

Status: proposed, not yet implemented

Issues: follow-up to `specs/plans/scheduler-event-loop-blocking.md` (implemented 2026-07-30, fixed
a 2.86s/4.86s stall by moving `evaluate_constraints_and_merits` onto a dedicated
`ThreadPoolExecutor`). A smaller residual stall (0.61s/2.61s) was seen on `iagvt`'s `scheduler`
module on 2026-08-05 with that fix already active — see
`specs/steering/scheduler-cpu-bound-merit-evaluation-stalls-event-loop.md` for the diagnosis this
plan acts on.

## Problem

The existing fix moved constraint/merit evaluation to a worker *thread*, not a worker *process*.
A thread still shares the GIL with the event loop's own thread, so CPU-bound astropy/numpy work in
that thread can still starve the main thread of interpreter time — smaller than a fully synchronous
call directly on the loop, but not zero. Real process isolation would close this gap, but
`run_cpu_bound` can't just swap `ThreadPoolExecutor` for `ProcessPoolExecutor` today, because
`DataProvider.archive` (an `ObservationArchiveEvolution`) does real async network I/O
mid-computation — `observations_for_task()`/`observations_for_night()` call
`await self._obs_archive.get_observations(...)` against a comm-backed proxy, lazily, on cache miss.
A child process can't share that live connection object.

## Goal

Make constraint/merit evaluation's *only* dependency on live state be plain, already-fetched,
picklable data — so moving the executor to a process becomes a mechanical, low-risk change instead
of a redesign. This plan covers the split; actually flipping `ThreadPoolExecutor` to
`ProcessPoolExecutor` is the last, smallest step and can be deferred/measured separately once the
split alone is shipped and stable (it's valuable on its own: it removes hidden I/O races from the
worker path even if the executor stays a thread pool).

## Considered options

**Where to draw the prefetch/evaluation boundary:**

1. **Prefetch per-timestep, right before each `run_cpu_bound` call.** Matches current call
   granularity exactly, but re-fetches the same task/night data on every one of the ~288 steps in
   a 24h schedule at 300s resolution — reintroduces the redundant-refetch problem the existing
   `DataProvider` caching was already built to avoid (`ObservationArchiveEvolution`'s dicts persist
   across the whole `schedule()` call precisely so this doesn't happen). Rejected.
2. **Prefetch once per `schedule()` call, covering the full task list and the full time window.**
   The task list (`self._tasks`, passed into `schedule()` and never mutated mid-call — confirmed:
   `schedule_in_interval`'s loop only calls `task.reset_resolved_target()` on the existing list, it
   never adds tasks) and the `[start, end]` window are both known before any evaluation happens.
   One prefetch pass up front matches the cache's existing lifetime (one `ObservationArchiveEvolution`
   per `schedule()` call, per its own docstring) exactly. **Chosen.**
3. **Prefetch lazily but off the worker thread** (e.g. a background asyncio task that races ahead
   of the evaluation and populates the cache just-in-time). More complex, and still leaves a real
   possibility of a genuine cache-miss race under concurrent access — rejected in favor of the
   simpler up-front pass, since option 2's one-time cost is small relative to a whole schedule
   computation anyway.

**How to make a cache miss inside the worker impossible to ignore:**

1. **Leave `observations_for_task`/`observations_for_night` as-is** (fetch-on-miss). Works today
   only because the thread shares memory with the main thread's `_obs_archive` object — silently
   stops working the moment anyone swaps in a process pool, with no error, just wrong/stale
   results (empty observation lists) computed from a `_obs_archive` that doesn't exist in the child
   process. Rejected — this is exactly the kind of bug that's invisible until it ships.
2. **Add a `freeze()` step**: after prefetch, mark `ObservationArchiveEvolution` frozen; any
   subsequent call to `observations_for_task`/`observations_for_night` for a key not already in the
   dict raises `RuntimeError` instead of falling back to `self._obs_archive`. Turns "quietly wrong
   under a process pool" into "loudly wrong under a thread pool, today, before the executor is ever
   touched." **Chosen** — validate this with the *existing* `ThreadPoolExecutor` first; only move to
   `ProcessPoolExecutor` once a real run (tests + a live schedule computation) produces zero
   `RuntimeError`s.

## Decision

### 1. `ObservationArchiveEvolution` — add prefetch + freeze (`observationarchiveevolution.py`)

```python
class ObservationArchiveEvolution:
    def __init__(self, observer: Observer, obs_archive: ObservationArchive | None = None):
        self._obs_archive = obs_archive
        self._obs_for_task: dict[Any, ObservationList] = {}
        self._obs_for_night: dict[datetime.date, ObservationList] = {}
        self._observer = observer
        self._frozen = False

    async def prefetch(self, tasks: Iterable[Task], nights: Iterable[datetime.date]) -> None:
        """Populates the task/night caches up front. Call once per schedule() run, before any
        evaluation happens, then freeze(). Runs on the caller's event loop (real I/O)."""
        for task in tasks:
            await self.observations_for_task(task)
        for night in nights:
            await self.observations_for_night(night)

    def freeze(self) -> None:
        """After this, a cache miss is a bug (missing from the prefetch set), not something to
        paper over with a live fetch — raises instead of silently reaching for `_obs_archive`,
        which may not exist once evaluation runs off-thread/off-process."""
        self._frozen = True
```

Modify `observations_for_task`/`observations_for_night`'s existing `if task.id not in
self._obs_for_task:` / `if date not in self._obs_for_night:` branches: if `self._frozen` and the
key is missing, `raise RuntimeError(f"... not prefetched before freeze() ...")` instead of falling
through to `self._obs_archive.get_observations(...)`.

### 2. Compute the night set — `ondemandscheduler.py`

`schedule()` knows `start`/`end` before calling `schedule_in_interval`. Add a small helper (new
function in `ondemandscheduler.py` or a `DataProvider` method) that walks `[start, end]` in
`_nightly step` (reuse whatever cadence `schedule_in_interval` already steps by, or just sample at
each calendar day boundary in range plus one day of margin on each side, since a "night" can span
across a UTC-day boundary) and collects the distinct `data.night(t)` values seen. For an ordinary
~24h `schedule_range`, this resolves to one, maybe two, `date` values — cheap regardless of
resolution chosen, so bias towards a safe, slightly-too-fine sampling rather than trying to compute
sunset/sunrise boundaries exactly.

### 3. Call prefetch + freeze — `ondemandscheduler.py`, `schedule()`

```python
async def schedule(self, tasks, projects, start, end, data):
    projects_dict = {project.code: project for project in projects}
    nights = self._nights_in_range(start, end)  # new helper from step 2
    await data.archive.prefetch(tasks, nights)
    data.archive.freeze()

    async for task in self.schedule_in_interval(tasks, projects_dict, start, end, data):
        yield task
        await data.archive.evolve(task)
```

`evolve()` (called after `yield`, still main-thread-side, same as today) appends the newly-scheduled
task's synthetic observation directly into `_obs_for_task`/`_obs_for_night` — it already does this
without touching `_obs_archive` as long as the key exists (which it now always will, post-prefetch),
so `evolve()` needs no change beyond continuing to work under `freeze()` (verify it never hits the
now-raising branch — it calls `observations_for_task` first specifically to ensure the key exists,
which after prefetch it always does).

### 4. Confirm zero cache misses before touching the executor

Run the full scheduler test suite plus a real `schedule()` call against production-shaped data
(existing `iagvt` config, or a synthetic task list matching its scale) with `freeze()` active and
the *current* `ThreadPoolExecutor` unchanged. Any `RuntimeError` here means step 2's night-range
computation or step 1's task-list assumption missed a real case — fix those before proceeding, not
by loosening `freeze()`.

### 5. Only after step 4 is clean: swap the executor (`_executor.py`)

```python
_executor = ProcessPoolExecutor(max_workers=1)
```

Requires, additionally:

- `coro_fn` (`self.evaluate_constraints_and_merits`, a bound method) and all `*args` (`tasks`,
  `projects`, `start`, `end`, `data`) must be picklable. `Task`/`Project` are pydantic `BaseModel`s
  (`pyobs/robotic/task.py`) — picklable by default barring a non-picklable field. `Constraint`/
  `Merit` are `PolymorphicBaseModel`s (same family) — same expectation, but every concrete
  constraint/merit needs an actual pickle round-trip check, not an assumption, since a future one
  could capture something live (a callback, a comm handle) without it being obvious from the base
  class.
- `DataProvider.archive` must not carry `_obs_archive` (the live comm proxy) across the process
  boundary — since `freeze()` guarantees it's never read again after prefetch, either null it out
  before dispatch (`data.archive._obs_archive = None`, ugly but minimal) or split it into a
  separate lightweight, picklable snapshot type that `DataProvider` swaps to after `freeze()`
  (cleaner, slightly more code — worth it if this plan's step 1 grows any more responsibilities
  later). Pick the snapshot-type approach if step 1 is implemented fresh; the null-out is only
  acceptable as a minimal patch on top of the existing class.
- `astroplan.Observer` (held by `DataProvider`) needs a pickle round-trip check too — expected to
  be fine (it's built from an `EarthLocation` plus scalar pressure/temperature/humidity, all plain
  data), but not yet verified in this codebase.
- `asyncio.run(coro_fn(*args))` inside a *process* re-creates not just a new event loop but a whole
  new interpreter — confirm nothing in the call chain relies on process-global state set up by the
  main process (e.g. `astropy.utils.iers.conf` from `_disable_iers_auto_download()` at startup,
  since a fresh interpreter starts with astropy's defaults, not whatever the parent process
  configured). If `iers_offline` is active, the child process needs the same `iers_conf` mutation
  applied — likely via an initializer passed to `ProcessPoolExecutor(initializer=...)`.

## Tests

### New tests required

- `tests/robotic/scheduler/test_observationarchiveevolution.py` (new, or extend existing coverage
  if a file already exercises this class — check first): `prefetch()` populates both dicts for a
  given task/night set without calling `_obs_archive.get_observations` more than once per key;
  `freeze()` then `observations_for_task` on an unprefetched task id raises `RuntimeError`;
  `evolve()` after `freeze()` succeeds for an already-prefetched task and does not reach for
  `_obs_archive`.
- `tests/robotic/scheduler/test_ondemandscheduler.py`: extend the existing `schedule()`-level
  tests to assert prefetch happens before the first `evaluate_constraints_and_merits` call (e.g.
  via call-order assertions on a mock `ObservationArchive`), and that a schedule spanning a
  day-boundary correctly resolves to the right multi-night set from step 2's helper.
- Once step 5 lands: a pickle round-trip test — `pickle.loads(pickle.dumps(x))` for a real
  `OnDemandScheduler`, `DataProvider` (post-freeze), `Task`, `Project`, and every concrete
  `Constraint`/`Merit` subclass in `pyobs/robotic/scheduler/{constraints,merits}/*.py` — run this
  as its own test independent of actually exercising `ProcessPoolExecutor`, so a future new
  constraint/merit that breaks picklability fails fast with a clear cause instead of surfacing as
  a mysterious `ProcessPoolExecutor` error.
- `pyrefly` check on all touched files ([[feedback_use_pyrefly_not_mypy]]).

### Existing coverage

`tests/robotic/scheduler/test_ondemandscheduler.py`'s existing `find_next_best_task`/
`check_for_better_task`/`can_postpone_task` tests exercise real constraint/merit evaluation
end-to-end already — re-run these after step 1-3 land as the first correctness check (this is a
refactor of *how* data reaches evaluation, not of the evaluation logic itself, so these should pass
unchanged; any failure here means the prefetch/freeze split broke something functional, not just
process-isolation groundwork).

## Consequences

- **Good:** the archive-access bug class this plan closes (silent empty-result fallback under a
  process pool) becomes impossible to ship unnoticed — `freeze()` converts it to a loud, immediate
  test failure.
- **Good:** step 1-4 are independently valuable even if step 5 (the `ProcessPoolExecutor` swap)
  never happens or is deferred — they remove a hidden I/O dependency from code that already
  pretends to be pure-CPU (`run_cpu_bound`'s own docstring says as much: "coro_fn... does not
  itself need to run on the caller's event loop"), which was already slightly false before this
  plan and becomes actually true after it.
- **Risk:** the night-range helper (step 2) must be conservative — an under-computed range causes
  a `RuntimeError` under `freeze()` (loud, step 4 catches it) rather than silent wrong data, so the
  failure mode here is safe, just potentially requires iterating on the sampling approach once
  tested against real multi-day schedules.
- **Risk, deferred to step 5's own review:** process-per-schedule-call overhead (interpreter
  startup, full re-import of astropy/astroplan/pyobs in the child) is unmeasured. If it's large
  relative to the CPU work being isolated, `max_workers=1` with a **persistent** process (reused
  across calls, not spawned fresh each time) would be the fix — `ProcessPoolExecutor` already
  reuses its worker process across submissions by default, so this should be fine, but worth
  confirming with a timing comparison against the current `ThreadPoolExecutor` before treating step
  5 as done.
- **Out of scope:** this plan doesn't change `AstroplanScheduler` (already subprocess-isolated via
  a different mechanism, per `specs/plans/scheduler-event-loop-blocking.md` §4) or any
  constraint/merit's internal logic.
