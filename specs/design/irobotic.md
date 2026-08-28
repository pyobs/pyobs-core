# `IRobotic` / `IRoboticScheduler`: executor and planner widgets for robotic modules

Status: proposed (issue #825).

Repos: pyobs-core (interfaces, `Mastermind`, `Scheduler`), pyobs-gui (`RoboticWidget`,
`ScheduleWidget`).

## Problem

The robotic pipeline is made of modules that run a schedule, and from the GUI there is no way
to control or inspect them:

- **`Mastermind`** (`pyobs/modules/robotic/mastermind.py`) executes the schedule: it pulls the
  next `Observation` from an `ObservationArchive` and runs it via a `TaskRunner`. It implements
  `IAutonomous` → `IStartStop` → `IRunning`, so the only remotely visible state is a boolean
  `RunningState`. It emits `TaskStartedEvent` / `TaskFinishedEvent` / `TaskFailedEvent`
  (name + id, plus ETA on start).
- **`Scheduler`** (`pyobs/modules/robotic/scheduler.py`) plans the schedule: it computes
  observations into the `ObservationArchive` and implements `IStartStop` + `IRunnable`
  (`run()` = re-schedule now). Again, only `IRunning` on the wire.

Consequences:

- No GUI widget exposes start/stop for either module; the only robotic-related UI is a passive
  warning label (`pyobs-gui/pyobs_gui/mainwindow.py:_check_warnings`) that polls
  `IAutonomous` clients' `IRunning` state every 5 s.
- The schedule/task data lives in module-internal child objects (`ObservationArchive` /
  `TaskArchive`) that are not reachable over comm. A client can only reconstruct a partial
  picture from the three task events, which carry name/id (+ ETA on start) only.

## Why two interfaces, not one

Both modules read and write the **same** `ObservationArchive` — Mastermind even writes the
in-progress observation back into it (state, start/end, obsnum), so the archive is the shared
source of truth. A single interface implemented by both would therefore make the two module
tabs show identical data (same current task, same schedule list) — redundant. The genuinely
role-owned data differs:

| | Mastermind (executor) | Scheduler (planner) |
|---|---|---|
| owns | the task it is executing right now (in-memory `_task`, `_task_target`, `_obsnum`, ETA) and **why a task can't run** (`TaskRunner.cant_run_reason`, tracked as `_last_cant_run_reason`) | the **plan** it computed and the action to **recompute it** (`IRunnable.run()`) |
| additionally knows | the immediate next observation it will pick up (`ObservationArchive.get_next_observation` every loop) | — |
| must not expose | the full schedule (shared data; would duplicate the planner tab) | current-task execution detail (only knows task IDs from `TaskStartedEvent`) |

So each interface exposes only what its module genuinely owns, and each GUI tab shows only
that.

## Interface shape

Both interfaces live in `pyobs/interfaces/` and inherit `IStartStop` (which already provides
`start()` / `stop()` and the `IRunning` `RunningState`). `RoboticTask` is a deliberately small
summary of an observation — never the full pydantic `Task`/`Observation` models, so large
schedules don't go over the wire.

### `IRobotic` — executor role (`Mastermind` only)

```python
@dataclass
class RoboticTask:
    id: Any
    name: str
    target: str | None = None      # target name, resolved if available
    start: Time | None = None      # planned start (next) / actual start (current)
    end: Time | None = None        # planned end / ETA
    obsnum: str | None = None      # "20260810-001" once assigned by Mastermind
    state: ObservationState | None = None
    priority: float | None = None

@dataclass
class RoboticState:
    running: bool
    current: RoboticTask | None = None
    next: RoboticTask | None = None             # immediate next observation to run
    cant_run_reason: str | None = None          # from TaskRunner.cant_run_reason()
    time: Time = field(default_factory=Time.now)

class IRobotic(IStartStop, metaclass=ABCMeta):
    state = RoboticState

    @abstractmethod
    async def get_status(self, **kwargs: Any) -> RoboticState: ...
```

- `next` is the immediate next observation the executor will start — deliberately *not* the
  full schedule; it pairs with `cant_run_reason` to answer "what's next and why are we
  waiting?".
- `state` on the interface class makes the state pushable over comm (`comm.set_state`), the
  same mechanism `IRunning` uses.

### `IRoboticScheduler` — planner role (`Scheduler` only)

```python
@dataclass
class SchedulerState:
    running: bool
    last_reschedule: Time | None = None
    time: Time = field(default_factory=Time.now)

class IRoboticScheduler(IStartStop, metaclass=ABCMeta):
    state = SchedulerState

    @abstractmethod
    async def get_schedule(self, limit: int = 20, **kwargs: Any) -> list[RoboticTask]: ...
```

- `get_schedule()` returns pending/in-progress entries only, trimmed to `limit`; the full
  `ObservationList` must not go over the wire.
- Re-schedule stays on the existing `IRunnable.run()` — no new method, the GUI calls it via
  proxy.

## Module implementations

### `Mastermind`

`class Mastermind(Module, IAutonomous, IRobotic, IFitsHeaderBefore)`. Publish `IRobotic`
state on `open()`, `start()`, `stop()`, and on every task transition in `_run_thread`
(started / finished / failed). All fields are already in memory:

- `current` ← `self._task`, `self._task_target`, `self._obsnum` (+ ETA from `task.duration`);
- `next` ← `self._observation_archive.get_next_observation(now, self._task_archive)`;
- `cant_run_reason` ← `self._last_cant_run_reason` (latest reason from
  `TaskRunner.cant_run_reason`).

`get_status()` assembles the same values on demand (initial load / refresh).

### `Scheduler`

`class Scheduler(Module, IStartStop, IRunnable, IRoboticScheduler)`. Publish `SchedulerState`
on `open()`, `start()`, `stop()`, and after each `_schedule_worker` pass (`last_reschedule`).
`get_schedule()` delegates to `self._schedule.get_schedule()`, maps observations to
`RoboticTask`, filters to pending/in-progress, trims to `limit`.

## GUI widgets

Two widgets in `pyobs-gui/pyobs_gui/`, following the `BaseWidget` pattern
(`autofocuswidget.py`, `acquisitionwidget.py`), registered per interface in
`mainwindow.DEFAULT_WIDGETS` so each module automatically gets its own tab:

- **`RoboticWidget`** (registered on `IRobotic`): running indicator, Start/Stop, current-task
  panel (name, id, target, started, ETA/countdown, obsnum), next-up + `cant_run_reason`
  ("waiting for weather / window not open yet").
- **`ScheduleWidget`** (registered on `IRoboticScheduler`): schedule table (start, end, task,
  target, state, priority), "Re-schedule now" button (proxy → `run()`), Start/Stop.

Data flow: `subscribe_state(module, <interface>, ...)` for steady state,
`register_event(TaskStartedEvent/TaskFinishedEvent/TaskFailedEvent)` for instant updates,
proxy calls for `start` / `stop` / `get_status` / `get_schedule` / `run`. Buttons gated by
ACLs via `self.permitted(...)` (see `pyobs-gui/specs/plans/2026-07-29-gui-acl-aware-widget-gating.md`).

## Out of scope

- Abort/pause the currently running task — no server-side path exists (`TaskRunner` has only
  `can_run()` / `run_task()`); follow-up.
- Manual scheduling / task editing from the GUI — pyobs-portal territory.
- Migrating `mainwindow._check_warnings` to the new state; the `IAutonomous`-keyed warning
  label stays as-is for now.

## Open questions

1. Interface names: `IRobotic` / `IRoboticScheduler` vs alternatives (`IRoboticExecutor`,
   `IScheduleRunner`, ...).
2. `get_schedule(limit)` default and hard cap (wire-size concern).
3. Extend `TaskFinishedEvent` / `TaskFailedEvent` with the obsnum, so a history view can link
   to the archive.
4. State publish cadence: transitions only, or a slow heartbeat so a dead module is
   distinguishable from an idle one.

## What a plan would need to cover

1. Interface files + exports + dataclass serialization (round-trip tests).
2. `Mastermind` state publishing (transitions in `_run_thread`) and `get_status`.
3. `Scheduler` state publishing and `get_schedule` trimming.
4. `RoboticWidget` + `ScheduleWidget` implementations and `DEFAULT_WIDGETS` registration.
5. Tests: state round-trip, publish transitions, schedule trimming; GUI fake-comm tests per
   `pyobs-gui/tests/test_mainwindow_startup.py` patterns.
