# Plan: Split archive prefetch from CPU-bound merit evaluation, to unblock a `ProcessPoolExecutor`

Status: partially implemented — steps 1-3 (prefetch + freeze) implemented 2026-08-06 to fix the
`run_cpu_bound` + aiohttp session event-loop conflict. Step 4 (`ProcessPoolExecutor` swap) deferred
until real GIL contention is confirmed by a stress test or real fleet growth.

Issues: follow-up to `specs/plans/scheduler-event-loop-blocking.md` (implemented 2026-07-30, fixed
a 2.86s/4.86s stall by moving `evaluate_constraints_and_merits` onto a dedicated
`ThreadPoolExecutor`). A smaller residual stall (0.61s/2.61s) was seen on `iagvt`'s `scheduler`
module on 2026-08-05 with that fix already active — see
`specs/steering/scheduler-cpu-bound-merit-evaluation-stalls-event-loop.md` for the diagnosis this
plan acts on.

## Update 2026-08-05: motivating incident had a different cause; this plan's premise is unconfirmed

Live `py-spy dump` capture of the actual 2026-08-05 incident (see the steering doc) found the
stall's real cause was `ObservationArchiveEvolution.evolve()` doing an uncached astropy sunset
lookup directly on the **main** thread, unrelated to `run_cpu_bound`'s worker thread entirely —
fixed in `pyobs-core` `2.0.0.dev65` by keying the lookup off the task's own scheduled time
(`data.night(task.start)`, reusing `DataProvider`'s existing cache) instead of recomputing from
`Time.now()` on every call.

That means the GIL-contention-in-the-worker-thread mechanism this plan exists to fix (see
"Problem" below) has **zero confirmed occurrences** on this system — we looked for it directly and
found something else instead. The reasoning for why it's plausible in general still holds (a
`ThreadPoolExecutor` genuinely doesn't give process-level GIL isolation), but "plausible in
general" isn't enough justification for the size of this plan (new `freeze()` machinery, a
picklable snapshot type, pickle round-trip tests for every constraint/merit,
`ProcessPoolExecutor`-initializer handling for `iers_conf`, etc.) without a real, observed instance
driving it.

**Why not just close it outright**: the mechanism scales with task count.
`evaluate_constraints_and_merits` does `tasks × constraints/merits × timesteps` of work per
schedule run — more tasks means more total CPU-bound time in that worker thread per call, and more
opportunity for any GIL-starvation effect to bite, even though it didn't show up at `iagvt`'s
current scale (~50 blocks/run). "No evidence at 50 blocks" doesn't mean "no risk at 500."

**Recommended next step, cheaper than implementing this plan**: a synthetic stress test —
generate a task list well beyond `iagvt`'s current scale (a few hundred blocks), run `schedule()`
against it, and watch with `py-spy` (or the existing event-loop-lag watchdog) for whether the
`pyobs-scheduler_0` worker thread — not the main thread this time — actually shows up active during
a stall. That directly answers "does this get worse with scale" with real evidence, at a fraction
of the cost of building the full split:

- If the stress test confirms GIL contention in the worker thread at some task-count threshold,
  this plan becomes justified by actual evidence and worth implementing (possibly gated on that
  threshold rather than done unconditionally).
- If even a large synthetic load shows nothing, that's a much stronger basis for closing this plan
  outright than the absence of evidence at today's real-world scale alone.

Not yet run. This plan stays on hold until one or the other happens.

## Update 2026-08-15: second occurrence, still unconfirmed

A new stall was logged on 2026-08-15 03:13 on the `scheduler` module (2.24s single check, 4.24s
total), in the same "Finished calculating next task" → "Finished calculating schedule for N
block(s)" window as both earlier incidents, with 44 blocks this run. The `evolve()` fix above is
already active, so this is the first observed stall where the previously-confirmed main-thread cause
can't explain it. That makes it *consistent with* the deferred step-4 mechanism (worker-thread GIL
contention), but it is **not confirmation** — no `py-spy` capture was taken, and the steering doc
documents a prior case where the same log-timing inference was wrong about which thread was at
fault.

Two details weaken the "scales with task count" framing: fewer blocks this run (44 vs 52) yet a
*larger* stall (2.24s/4.24s vs 0.61s/2.61s). The stress test + `py-spy` capture recommended above is
now the next action, not optional — a real occurrence of the symptom with the known main-thread
cause already ruled out is the trigger the plan said it was waiting for.

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
   subsequent call to `observations_for_task` for a key not already in the dict raises
   `RuntimeError` instead of falling back to `self._obs_archive`. Turns "quietly wrong under a
   process pool" into "loudly wrong under a thread pool, today, before the executor is ever
   touched." **Chosen** for `observations_for_task`. `observations_for_night` gets a different,
   more precise rule — see below — since unlike tasks (unbounded historical lookup, no way to
   prove a miss is safe), nights have a provable case where a miss is *not* a bug.

**Handling `observations_for_night` misses specifically:**

`observations_for_night` only ever returns `state=COMPLETED` observations, and `Scheduler`
(`scheduler.py:220-222`) always pins `start` to at least `_safety_time` past the real wall-clock
"now" the schedule computation is running at. Combining those two facts: `night(start)` — the
"current" night, anchored to the most recent sunset before `start` — is the *only* night that can
possibly have completed observations already on record (something could have run earlier this
same evening, before this `schedule()` call started). Any other night value that evaluation asks
for can only be a *later* one (time only ever advances through `schedule_in_interval`'s loop), and
a night that hasn't started yet by definition has zero completed observations — not "probably
zero," provably zero, given the `COMPLETED` filter.

So the fetch/freeze split for nights doesn't need to enumerate every night the loop might touch at
all:

1. Prefetch fetches exactly one night from the archive: `night(start)`.
2. `observations_for_night` on a miss (any date other than the one just fetched) doesn't raise —
   it seeds and returns a fresh empty `ObservationList` for that date, no I/O, safe to do even
   inside the frozen/offloaded evaluation path itself. `evolve()`'s later appends (when a task
   actually gets scheduled into that new night) accumulate against that empty bucket exactly like
   they already do for the first night today.

This removes the need for a night-range helper, and with it, the whole "how finely should we
sample `[start, end]` to enumerate nights" question — there was never a set of nights to
enumerate; there's one real fetch, and everything else self-resolves to empty by construction.
This relies on an explicit invariant that's worth a comment where it's implemented: **`start` is
never in the past relative to the schedule computation's own wall-clock time.** If some future
caller ever passes an already-past `start` (e.g. a backfill/what-if replay), this assumption breaks
silently (an empty result instead of the real historical one) rather than raising — flagged in
Consequences below as the one correctness risk this design accepts.

## Decision

### 1. `ObservationArchiveEvolution` — add prefetch + freeze (`observationarchiveevolution.py`)

```python
class ObservationArchiveEvolution:
    def __init__(self, observer: Observer, obs_archive: ObservationArchive | None = None):
        self._obs_archive = obs_archive
        self._obs_for_task: dict[Any, ObservationList] = {}
        self._obs_for_night: dict[datetime.date, ObservationList] = {}
        self._observer = observer
        self._current_night: datetime.date | None = None
        self._frozen = False

    async def prefetch(self, tasks: Iterable[Task], start: Time) -> None:
        """Populates the task cache and the one real night (anchored to `start`) up front. Call
        once per schedule() run, before any evaluation happens, then freeze(). Runs on the
        caller's event loop (real I/O)."""
        for task in tasks:
            await self.observations_for_task(task)
        self._current_night = self.night(start)
        await self.observations_for_night(self._current_night)

    def freeze(self) -> None:
        """After this: a task-id miss is a bug (missing from the prefetch set) and raises. A
        night miss is not a bug -- since `start` is guaranteed never in the past (Scheduler pins
        it at least `_safety_time` ahead of "now"), any night other than the one prefetched in
        `prefetch()` is strictly later and therefore provably has zero COMPLETED observations --
        seeded as an empty list instead of fetched or raised."""
        self._frozen = True
```

Modify `observations_for_task`'s existing `if task.id not in self._obs_for_task:` branch: if
`self._frozen` and the key is missing, `raise RuntimeError(f"... not prefetched before freeze()
...")` instead of falling through to `self._obs_archive.get_observations(...)`.

Modify `observations_for_night`'s equivalent branch: if `self._frozen` and `date` is missing,
seed `self._obs_for_night[date] = ObservationList()` and return it directly — no archive call, no
raise. (Add an assertion/log that `date > self._current_night` here, purely as a canary: if that
ever turns out false, the "`start` is never in the past" invariant above has been violated
somewhere and silently returning empty would be masking a real correctness bug rather than a safe
one — worth catching loudly even though the *steady-state* behavior for this branch is "return
empty, no error.")

### 2. Call prefetch + freeze — `ondemandscheduler.py`, `schedule()`

```python
async def schedule(self, tasks, projects, start, end, data):
    projects_dict = {project.code: project for project in projects}
    await data.archive.prefetch(tasks, start)
    data.archive.freeze()

    async for task in self.schedule_in_interval(tasks, projects_dict, start, end, data):
        yield task
        await data.archive.evolve(task)
```

No night-range helper needed — `prefetch()` only ever touches `night(start)` itself (see step 1).

`evolve()` (called after `yield`, still main-thread-side, same as today) appends the newly-scheduled
task's synthetic observation directly into `_obs_for_task`/`_obs_for_night` — it already does this
without touching `_obs_archive` as long as the key exists (which it now always will, either from
prefetch or from the empty-seed-on-miss path above), so `evolve()` needs no change beyond
continuing to work under `freeze()`.

### 3. Confirm zero cache misses before touching the executor

Run the full scheduler test suite plus a real `schedule()` call against production-shaped data
(existing `iagvt` config, or a synthetic task list matching its scale) with `freeze()` active and
the *current* `ThreadPoolExecutor` unchanged. Any `RuntimeError` here means step 1's task-list
assumption missed a real case (some task got evaluated that wasn't in the original `tasks` list) —
fix that before proceeding, not by loosening `freeze()`. The night side has no error path left to
watch for by design — the canary assertion above is the only thing to check there.

### 4. Only after step 3 is clean: swap the executor (`_executor.py`)

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
  boundary. **Decision: introduce a separate, always-picklable snapshot type** rather than nulling
  out `_obs_archive` on the existing class:

  ```python
  @dataclass
  class FrozenObservations:
      obs_for_task: dict[Any, ObservationList]
      obs_for_night: dict[datetime.date, ObservationList]
      current_night: datetime.date
  ```

  `DataProvider.archive` swaps from the live `ObservationArchiveEvolution` to a `FrozenObservations`
  at the same point `freeze()` happens today — `FrozenObservations` simply has no `_obs_archive`
  field to leak, rather than relying on remembering to null one out. `observations_for_task`/
  `observations_for_night`'s frozen-branch logic (task raises on miss, night seeds empty on miss)
  moves onto this type; `ObservationArchiveEvolution` itself only needs `prefetch()` and the
  swap-on-freeze, not the frozen-read logic. `evolve()` also needs to keep working against whichever
  of the two objects is current at call time.
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
  if a file already exercises this class — check first): `prefetch()` fetches every task id once
  and exactly one night (`night(start)`) without calling `_obs_archive.get_observations` more than
  once per key; `freeze()` then `observations_for_task` on an unprefetched task id raises
  `RuntimeError`; `freeze()` then `observations_for_night` on a *different* (later) date returns an
  empty `ObservationList` without touching `_obs_archive` at all (assert the mock archive's
  `get_observations` was never called again); `evolve()` after `freeze()` succeeds for both an
  already-prefetched task and a newly-seeded-empty night, for both without reaching for
  `_obs_archive`.
- `tests/robotic/scheduler/test_ondemandscheduler.py`: extend the existing `schedule()`-level
  tests to assert prefetch happens before the first `evaluate_constraints_and_merits` call (e.g.
  via call-order assertions on a mock `ObservationArchive`), and that a schedule spanning a
  day-boundary (some scheduled task pushing `time` in `schedule_in_interval`'s loop past the next
  sunset) correctly reads back an empty `FollowMerit`/`PerNightMerit` result for the new night
  rather than raising or reusing the first night's data.
- Once step 4 lands: a pickle round-trip test — `pickle.loads(pickle.dumps(x))` for a real
  `OnDemandScheduler`, `DataProvider` (post-freeze), `Task`, `Project`, and every concrete
  `Constraint`/`Merit` subclass in `pyobs/robotic/scheduler/{constraints,merits}/*.py` — run this
  as its own test independent of actually exercising `ProcessPoolExecutor`, so a future new
  constraint/merit that breaks picklability fails fast with a clear cause instead of surfacing as
  a mysterious `ProcessPoolExecutor` error.
- `pyrefly` check on all touched files ([[feedback_use_pyrefly_not_mypy]]).

### Existing coverage

`tests/robotic/scheduler/test_ondemandscheduler.py`'s existing `find_next_best_task`/
`check_for_better_task`/`can_postpone_task` tests exercise real constraint/merit evaluation
end-to-end already — re-run these after steps 1-2 land as the first correctness check (this is a
refactor of *how* data reaches evaluation, not of the evaluation logic itself, so these should pass
unchanged; any failure here means the prefetch/freeze split broke something functional, not just
process-isolation groundwork).

## Consequences

- **Good:** the archive-access bug class this plan closes (silent empty-result fallback under a
  process pool) becomes impossible to ship unnoticed — `freeze()` converts a task-id miss into a
  loud, immediate test failure, and a night miss is no longer even a fallible code path (it's
  provably safe to resolve to empty by construction, not just "not yet observed to fail").
- **Good:** steps 1-3 are independently valuable even if step 4 (the `ProcessPoolExecutor` swap)
  never happens or is deferred — they remove a hidden I/O dependency from code that already
  pretends to be pure-CPU (`run_cpu_bound`'s own docstring says as much: "coro_fn... does not
  itself need to run on the caller's event loop"), which was already slightly false before this
  plan and becomes actually true after it.
- **Good:** dropping the night-range helper entirely (rather than tuning its sampling resolution)
  removes a whole category of "did we enumerate enough nights" risk that an earlier version of
  this plan carried — there's no set to enumerate, so there's nothing to under-compute.
- **Risk, explicit invariant to document in code:** the empty-seed-on-miss behavior for nights
  depends on `start` never being in the past relative to the schedule computation's own wall-clock
  time (true today via `Scheduler`'s `_safety_time` margin). If a future caller ever passes an
  already-past `start`, this degrades to silently wrong (empty) results for a night that could have
  real history, rather than raising — the canary assertion in step 1 (`date > self._current_night`)
  is the guard against this, but it's an assertion on a code path whose normal behavior is "return
  empty, no error," so it's worth a deliberate second look in review rather than assuming the test
  suite alone will catch a violation.
- **Risk, deferred to step 4's own review:** process-per-schedule-call overhead (interpreter
  startup, full re-import of astropy/astroplan/pyobs in the child) is unmeasured. If it's large
  relative to the CPU work being isolated, `max_workers=1` with a **persistent** process (reused
  across calls, not spawned fresh each time) would be the fix — `ProcessPoolExecutor` already
  reuses its worker process across submissions by default, so this should be fine, but worth
  confirming with a timing comparison against the current `ThreadPoolExecutor` before treating step
  4 as done.
- **Out of scope:** this plan doesn't change `AstroplanScheduler` (already subprocess-isolated via
  a different mechanism, per `specs/plans/scheduler-event-loop-blocking.md` §4) or any
  constraint/merit's internal logic.
