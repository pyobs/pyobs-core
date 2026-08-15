# Plan: Stop scheduler constraint/merit evaluation from blocking the event loop

Status: implemented
Issues: none — found via live incident diagnosis (`(scheduler) module.py:205/207 "Event loop
stalled for 2.86s"` / `"...recovered after being stalled for 4.86s total."`, 2026-07-30, on a
`pyobs.modules.robotic.Scheduler` module named `scheduler`, using `OnDemandScheduler`)

## Problem

`Module._watch_event_loop_lag` (`pyobs/modules/module.py:183-208`) detected a multi-second event
loop stall on the `scheduler` module. Root cause: `OnDemandScheduler.schedule_in_interval` /
`check_for_better_task` (`pyobs/robotic/scheduler/ondemandscheduler.py:81-282`) re-evaluate every
constraint and merit for every schedulable task at every 300s step across the full
`schedule_range` (default 24h ≈ 288 steps), via `evaluate_constraints_and_merits`
(`ondemandscheduler.py:206-246`).

Every `Constraint.__call__` and `Merit.__call__` is declared `async def` but never actually
awaits anything — they call straight into synchronous `astroplan.Observer`/`astropy` work
(`observer.altaz`, `astropy.coordinates.get_body("moon", ...)`,
`observer.target_meridian_transit_time`, `observer.midnight`, etc. — see
`pyobs/robotic/scheduler/constraints/*.py`). `DataProvider`
(`pyobs/robotic/scheduler/dataprovider.py`) only caches `last_sunset`/`last_sunrise`/`night`, so
every one of these calls redoes a full astropy computation. With a real fleet-sized task list,
that's `tasks × steps × constraints` of uncached, un-yielded CPU work run back-to-back — nothing
ever suspends, so the event loop (and everything else sharing this module's process — comm RPC,
other background tasks) is blocked until the whole pass finishes.

`trigger_on_every_update: True` (the config on the affected instance) means this isn't a rare
event — it fires on effectively every task-archive poll.

Sibling `AstroplanScheduler` (`pyobs/robotic/scheduler/astroplanscheduler.py:125-148`) already
solves an analogous problem by running its scheduling pass in a subprocess and awaiting it via
`loop.run_in_executor(None, queue_out.get, True)` — confirms "this kind of computation must leave
the event loop" is the established shape of fix in this codebase, not a new idea.

## Goal

Make `OnDemandScheduler`'s per-timestep evaluation loop stop blocking the event loop, and reduce
the redundant astropy computation driving the cost in the first place, without changing the
public async `Constraint`/`Merit` API (so a future constraint that genuinely needs async I/O,
e.g. a weather-service lookup, still works). Fix should live at a level shared by any
`TaskScheduler` implementation built on `Constraint`/`Merit`, not be `OnDemandScheduler`-specific.

## Considered options

**Offload granularity** (what unit of work gets pushed off the event loop):

1. **Per constraint/merit call.** Simplest conceptually, but `evaluate_constraints_and_merits` can
   call dozens of these per task per step — thousands of thread-pool round trips per schedule
   computation, with submission/context-switch overhead likely exceeding the savings. Rejected.
2. **Whole `schedule()` pass in a subprocess**, following `AstroplanScheduler`'s precedent.
   Rejected: `OnDemandScheduler.schedule_in_interval` is an async generator that submits the
   *first* found task immediately (`schedule.py:244-254` — sets `_safety_time` and calls
   `add_observations` as soon as the first result is known, before the rest of the schedule is
   computed) so the fleet gets a next-task ASAP instead of waiting for the full 24h schedule.
   Moving the whole pass to a subprocess means either batching all output (losing that early-yield
   behavior) or building incremental subprocess→main-loop streaming — disproportionate for this
   problem.
3. **`evaluate_constraints_and_merits` as the offload unit** (once per task-list per timestep —
   called from `find_next_best_task:253`, `check_for_better_task:277`, `can_postpone_task:298`).
   Matches the granularity already used elsewhere in this codebase for CPU-bound work (`pysep.py:255`,
   `daophot.py:145`, `aperture_photometry.py:48` — offload one bounded synchronous unit per
   `await`, not per sub-call). Preserves the incremental-yield behavior of `schedule_in_interval`,
   since only the innermost evaluation is offloaded, not the whole generator. **Chosen.**
4. **Drop `async` from `Constraint`/`Merit.__call__`, call directly inside `run_in_executor`.**
   Mechanically simpler (no nested event loop needed), but changes the abstract API every
   constraint/merit (including any user-written ones) implements, and forecloses a
   legitimately-async constraint in the future. Rejected as more invasive than necessary for what
   is, today, a purely synchronous call chain in practice.

Since option 3 offloads a call chain that is itself `async def` (it awaits `task.resolve_target`,
`constraint(...)`, `merit(...)`), the offloaded thread needs its own event loop to run it:
`asyncio.run(self.evaluate_constraints_and_merits(...))` inside the executor thread.

## Decision

### 1. Dedicated executor — new file `pyobs/robotic/scheduler/_executor.py`

```python
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

_T = TypeVar("_T")

# single worker: evaluate_constraints_and_merits calls are always awaited sequentially by the
# caller (never fired concurrently), and DataProvider's functools.cache is not safe under real
# concurrent access -- one worker keeps that access serialized while still freeing the main loop.
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pyobs-scheduler")


async def run_cpu_bound(coro_fn: Callable[..., Awaitable[_T]], *args: object) -> _T:
    """Runs an async callable to completion on a dedicated worker thread, off the caller's loop.

    Args:
        coro_fn: An async callable whose body does not itself need to run on the caller's
            event loop (no dependency on the caller's other tasks, timers, or comm state).
        args: Positional args for coro_fn.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, lambda: asyncio.run(coro_fn(*args)))
```

Kept in `robotic/scheduler/` (not `utils/`) since it's specific to this synchronous-work-disguised-
as-async pattern in constraint/merit evaluation, not a general-purpose helper.

### 2. Offload the three call sites — `pyobs/robotic/scheduler/ondemandscheduler.py`

```python
from ._executor import run_cpu_bound
```

- `find_next_best_task:253` —
  `merits = await run_cpu_bound(self.evaluate_constraints_and_merits, tasks, projects, start, end, data)`
- `check_for_better_task:277` — same substitution inside its `while` loop.
- `can_postpone_task:298` — same substitution.

No signature changes to `evaluate_constraints_and_merits`, `evaluate_constraints`,
`evaluate_merits`, or any `Constraint`/`Merit`. `self` and `data` are passed by reference (threads
share memory, unlike the subprocess case) — no pickling concerns.

### 3. Cache target-independent astropy results — `pyobs/robotic/scheduler/dataprovider.py`

Add, alongside the existing `@cache`d `last_sunset`/`last_sunrise`/`night`:

```python
@cache
def sun(self, time: Time) -> SkyCoord: ...        # astropy.coordinates.get_sun(time)

@cache
def sun_altaz(self, time: Time) -> Any: ...        # self.observer.sun_altaz(time)

@cache
def moon(self, time: Time) -> SkyCoord: ...        # astropy.coordinates.get_body("moon", time)

@cache
def moon_illumination(self, time: Time) -> float: ...  # self.observer.moon_illumination(time)
```

Update `SolarElevationConstraint.__call__`, `MoonSeparationConstraint.__call__`/
`filter_skycoord`, `MoonIlluminationConstraint.__call__` to call these instead of
`data.observer`/`astropy.coordinates` directly. `Time.__hash__` already exists
(`pyobs/utils/time.py:20`), so this is a direct extension of the existing cache pattern, not a new
one.

This targets the redundancy that's actually there: every task at a given timestep shares the same
sun/moon position, so caching by `time` alone collapses `N tasks` worth of identical astropy calls
into one. **Out of scope:** target-dependent `AirmassConstraint`/`observer.altaz` caching — that
needs a per-`(time, target)` key, not just `time`, and is a bigger change for a less certain win.
Revisit only if the executor offload alone doesn't bring stalls under the watchdog's 0.5s
threshold in practice.

### 4. `AstroplanScheduler` — no change

Already off the event loop via its subprocess approach; unaffected by this plan.

## Tests

### Existing coverage (regression net, no changes needed)

Checked against the current suite before writing this plan:

- All three offload call sites are already exercised end-to-end with a real `astroplan.Observer`
  and concrete value assertions, in `tests/robotic/scheduler/test_ondemandscheduler.py`:
  `test_next_best_task` → `find_next_best_task`, `test_check_for_better_task` →
  `check_for_better_task`, `test_fill_for_better_task`/`test_postpone_task` →
  `can_postpone_task` (via `schedule_first_in_interval`). Since the offload wraps these methods'
  internal calls without changing their signatures or return values, this suite catches any value
  regression from the change (wrong result, swallowed exception changing control flow, etc.) —
  it just can't tell us whether the event loop stayed responsive while doing it.
- Every constraint touched by the new `DataProvider` caching already has a dedicated test file
  that calls it several times with distinct `Time` values against one shared `DataProvider`
  instance: `tests/robotic/scheduler/constraints/test_solarelevation.py`,
  `test_solarelevation_direction.py` (all three `direction` branches), `test_moonseparation.py`
  (including `filter_skycoord`), `test_moonillumination.py`. This is a solid regression net for
  cache *correctness* (right value per distinct time key) — it does not check cache *hit rate*,
  which is what the caching change is actually for.
- `tests/modules/robotic/test_scheduler.py` mocks `TaskScheduler` entirely
  (`MagicMock(spec=TaskScheduler)`), so it's unaffected either way — the `Scheduler` module
  boundary isn't touched by this plan.

Run the full existing suite (`pytest tests/robotic/scheduler/ tests/modules/robotic/`) after
implementing as the first correctness check, before adding anything new.

### New tests required (nothing existing covers these)

- `tests/robotic/scheduler/test_executor.py` (new): unit-test `run_cpu_bound` in isolation —
  a coroutine that raises a specific exception, awaited via `run_cpu_bound`, must re-raise the
  *same* exception type/message on the caller's side. This is the concrete risk: `_schedule_worker`
  (`pyobs/modules/robotic/scheduler.py:274-275`) relies on exceptions from
  `evaluate_constraints_and_merits` surviving the `run_in_executor` → `asyncio.run` →
  `run_in_executor` round trip — if that path swallowed or mangled an exception instead of
  propagating it, a broken constraint would fail silently instead of being logged. Also assert a
  successful call's return value comes back unchanged, and that it actually ran on a different
  thread (e.g. compare `threading.get_ident()` inside vs. outside).
- `tests/robotic/scheduler/test_ondemandscheduler.py`: add a test using a constraint that does
  `time.sleep(...)` (simulating CPU-bound work) inside `__call__`, run concurrently with an
  `asyncio` heartbeat task via `asyncio.gather`, and assert the heartbeat kept ticking on schedule
  while `scheduler.schedule(...)` was being consumed — proves the offload actually keeps the loop
  responsive, without depending on real astropy timing (which would make the test slow/flaky).
  Design it to go through all three offload call sites in one pass (reuse the
  `test_fill_for_better_task`/`test_postpone_task` task shapes, which already force
  `check_for_better_task` and `can_postpone_task` to run), not just `find_next_best_task`.
- New `tests/robotic/scheduler/test_dataprovider.py`: instrument `get_sun`/`get_body`/
  `Observer.sun_altaz`/`Observer.moon_illumination` with a call counter (monkeypatch or spy), call
  `sun`/`sun_altaz`/`moon`/`moon_illumination` twice with the same `time` and once with a
  different `time`, assert exactly 2 underlying calls (cache hit on the repeat, miss on the new
  time) — the actual point of the caching change, not just "does it return the right value."
  Also test that two separate `DataProvider` instances (as created fresh per `schedule()` call,
  `ondemandscheduler.py:66-67`) don't share cache state — a stale value leaking across schedule
  runs would be a real, currently-untested regression risk.
- `pyrefly` check on `_executor.py` and all touched files ([[feedback_use_pyrefly_not_mypy]]).

## Consequences

- **Good:** event loop stays responsive during schedule computation — the specific symptom that
  triggered this investigation goes away.
- **Good:** fix lives at the `evaluate_constraints_and_merits` / `DataProvider` level, so any
  future `TaskScheduler` built the same way benefits, not just `OnDemandScheduler`.
- **Good:** matches this codebase's existing "offload one bounded sync unit of work per `await`"
  precedent (`pysep.py`, `daophot.py`, `aperture_photometry.py`) rather than inventing a new shape.
- **Neutral:** first *dedicated* `ThreadPoolExecutor` in the codebase — every existing
  `run_in_executor` call uses the default (`None`) executor. Justified here by isolating scheduler
  CPU work from unrelated `run_in_executor` users sharing the process-wide default pool, and by
  needing an explicit `max_workers=1` for the reason in point 5 below.
- **Neutral:** `asyncio.run()` inside the worker thread creates a throwaway event loop per
  offloaded call (up to 3 per timestep). Overhead is small relative to the astropy work being
  offloaded, and calls only happen once per triggered schedule computation, not per RPC.
- **Risk:** `DataProvider`'s `functools.cache`d methods must only ever be called from inside the
  offloaded (single-worker) path, never concurrently from the main loop — future code touching
  `data.*` cached methods directly from other async code would reintroduce a race. Worth a
  docstring note on `DataProvider` itself.
- **Out of scope, flagged for follow-up:** target-dependent altaz caching (`AirmassConstraint`
  and similar) if the offload alone isn't enough to keep stalls under threshold at real fleet
  scale.
