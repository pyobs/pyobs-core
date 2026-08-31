# `IRobotic` / `IRoboticScheduler`: executor and planner widgets for robotic modules

Status: implemented, closed (issue #825). pyobs-core side (interfaces, `Mastermind`,
`Scheduler`) landed in [pyobs-core#826](https://github.com/pyobs/pyobs-core/pull/826), shipped in
`v2.1.0`. pyobs-gui side (`RoboticWidget`, `ScheduleWidget`) landed in
[pyobs-gui#155](https://github.com/pyobs/pyobs-gui/pull/155) — see
`pyobs-gui/specs/2026-08-31-irobotic-widgets.md`.

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
| owns | the task it is executing right now (in-memory `_task`, `_task_target`, `_obsnum`, ETA) and **why a task can't run** (`TaskRunner.cant_run_reason`, tracked alongside the blocked/skipped observation as `_cant_run_reason`/`_next_observation`) | the **plan** it computed and the action to **recompute it** (`IRunnable.run()`) |
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
    current: RoboticTask | None = None
    next: RoboticTask | None = None             # immediate next observation to run
    cant_run_reason: str | None = None          # from TaskRunner.cant_run_reason(), for `next`
    time: Time = field(default_factory=Time.now)

class IRobotic(IStartStop, metaclass=ABCMeta):
    state = RoboticState
```

- No `running` field: `IRobotic` already inherits `IRunning`'s `RunningState.running` via
  `IStartStop`; a second `running` bool here would be a second source of truth that a future
  transition can update one of and not the other. Widgets read the running flag from the
  `IRunning` state, same as they would for any other `IStartStop` module.
- No `get_status()` pull RPC: `RoboticState` is pushed via `comm.set_state` on every
  transition, and a subscriber gets the last-pushed value immediately on `subscribe_state`
  (XMPP pubsub delivers the last item, `max_items=1`, to a new subscriber). A bespoke pull
  method would duplicate that path for no benefit, and — since `next` is populated from
  `ObservationArchive.get_next_observation()`, which does a live portal HTTP call for
  `LcoObservationArchive` — an RPC-triggered pull would turn a GUI refresh into a network
  request that can hang or fail if the portal is slow or down.
- `cant_run_reason` is tracked as a scalar pair with `next` — `Mastermind._cant_run_reason` /
  `_next_observation` — updated together via a single `_track_next_observation(observation,
  reason)` helper, not read off a per-task dict. (An earlier draft of this field kept a
  `dict[task_id, str]` purely to dedupe repeated log lines; that had no defined mapping to a
  single scalar and is gone — the scalar pair now serves both the log dedup and the published
  state.) The helper republishes only when the observation (by task id, `start`, `end`) or the
  reason actually changed since the last publish, so `_run_thread`'s ~10s poll doesn't spam a
  state update while stuck on the same block. It's called from both places `_run_thread` can be
  stuck without transitioning: the "cannot run" branch (real `cant_run_reason`) and the
  late-start-skip branch (`cant_run_reason=None` — `TaskRunner.cant_run_reason()` was never
  consulted for that failure mode, so the field stays honest about what it actually reflects).
- `next` is the immediate next observation the executor will start — deliberately *not* the
  full schedule; it pairs with `cant_run_reason` to answer "what's next and why are we
  waiting?".
- `state` on the interface class makes the state pushable over comm (`comm.set_state`), the
  same mechanism `IRunning` uses.

### `IRoboticScheduler` — planner role (`Scheduler` only)

```python
@dataclass
class SchedulerState:
    last_reschedule: Time | None = None
    time: Time = field(default_factory=Time.now)

class IRoboticScheduler(IStartStop, metaclass=ABCMeta):
    state = SchedulerState

    @abstractmethod
    async def get_schedule(self, limit: int = 20, **kwargs: Any) -> list[RoboticTask]: ...
```

- No `running` field, same reasoning as `RoboticState` above — read it from the inherited
  `IRunning` state.
- `get_schedule()` returns pending/in-progress entries only, trimmed to `limit`; the full
  `ObservationList` must not go over the wire. `limit` defaults to 20, and the implementation
  enforces a hard server-side ceiling regardless of what a client requests — a client-supplied
  default alone doesn't stop a client from asking for everything.
- Re-schedule stays on the existing `IRunnable.run()` — no new method, the GUI calls it via
  proxy.

## Module implementations

### `Mastermind`

`class Mastermind(Module, IAutonomous, IRobotic, IFitsHeaderBefore)`. Publish `IRobotic`
state on `open()`, `start()`, `stop()`, on every task transition in `_run_thread`
(started / finished / failed), and — via `_track_next_observation()` — whenever the tracked
`next` observation or `cant_run_reason` actually changes while nothing is transitioning (stuck
on a "cannot run" block, or repeatedly skipping the same observation for starting too late):

- `current` ← `self._task`, `self._task_target`, `self._obsnum` (+ ETA from `task.duration`);
  already in memory, no extra query.
- `next` ← `self._next_observation`, set from whatever `_run_thread` last got back from
  `self._observation_archive.get_next_observation(now, self._task_archive)` — **not** free: for
  `LcoObservationArchive` this is a live portal HTTP call. Only call it from inside
  `_run_thread`, where it already runs every loop iteration regardless; never re-derive it on
  an RPC path (there is no `get_status()` — see above).
- `cant_run_reason` ← `self._cant_run_reason`, set alongside `_next_observation` by
  `_track_next_observation`: `self._task_runner.cant_run_reason(next.task)` when blocked, or
  `None` on a late-start skip (see the note above — that failure mode isn't sourced from
  `TaskRunner.cant_run_reason()`).

### `Scheduler`

`class Scheduler(Module, IRunnable, IRoboticScheduler)` — **not** `IStartStop` too: `IRoboticScheduler`
already inherits it, and listing it explicitly *before* a subclass of it is an invalid MRO (Python
raises `TypeError: Cannot create a consistent method resolution order`, confirmed against the real
`IRunnable`/`IAbortable`/`IStartStop` chain). Same reasoning as `Mastermind` not listing `IStartStop`
alongside `IAutonomous`/`IRobotic`. Publish `SchedulerState`
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

Data flow: `subscribe_state(module, <interface>, ...)` for steady state — a new subscriber
gets the last-pushed value immediately, so this also covers initial load / refresh, no
separate pull RPC needed — `register_event(TaskStartedEvent/TaskFinishedEvent/TaskFailedEvent)`
for instant updates, proxy calls for `start` / `stop` / `get_schedule` / `run`. Buttons gated by
ACLs via `self.permitted(...)` (see `specs/plans/2026-07-29-gui-acl-aware-widget-gating.md`, this
repo — implemented, closed).

## Out of scope

- Abort/pause the currently running task — no server-side path exists (`TaskRunner` has only
  `can_run()` / `run_task()`); follow-up.
- Manual scheduling / task editing from the GUI — pyobs-portal territory.
- Migrating `mainwindow._check_warnings` to the new state; the `IAutonomous`-keyed warning
  label stays as-is for now.

## Resolved questions

1. **Interface names**: keeping `IRobotic` / `IRoboticScheduler` — no alternative considered
   was clearly better.
2. **`get_schedule(limit)` default and cap**: default 20; implementation additionally enforces
   a hard server-side ceiling independent of the client-supplied `limit`, so a client can't
   request the full unbounded schedule.
3. **Obsnum on `TaskFinishedEvent`/`TaskFailedEvent`**: doing it now, not as a follow-up.
   `Mastermind._obsnum` is already computed before `TaskStartedEvent` fires
   (`pyobs/modules/robotic/mastermind.py:188` precedes the `send_event` at `:195`), so adding
   it to all three task events costs nothing extra.
4. **State publish cadence**: transitions only, no heartbeat. `Comm` already has a
   presence mechanism for module liveness independent of RPC/state
   (`set_presence`/`subscribe_presence`, `pyobs/comm/comm.py:544-673`, XMPP-backed), generic
   across every module. A widget-level heartbeat would duplicate that for these two modules
   only.

## What a plan would need to cover

pyobs-core side (1–4, and the pyobs-core half of 6) implemented in
[pyobs-core#826](https://github.com/pyobs/pyobs-core/pull/826):

1. ~~Interface files + exports + dataclass serialization (round-trip tests).~~ Done.
2. ~~`Mastermind` state publishing (transitions in `_run_thread`, plus `_track_next_observation`
   republishing on change while stuck without transitioning).~~ Done.
3. ~~`Scheduler` state publishing and `get_schedule` trimming + hard server-side cap.~~ Done
   (`get_schedule()` also resolves bare-FK-id tasks via `TaskArchive` for
   `PortalObservationArchive`, whose `get_schedule()` doesn't resolve them itself).
4. ~~Add `obsnum: str | None` to `TaskStartedEvent` / `TaskFinishedEvent` / `TaskFailedEvent`.~~
   Done.
5. ~~`RoboticWidget` + `ScheduleWidget` implementations and `DEFAULT_WIDGETS` registration.~~
   Done in [pyobs-gui#155](https://github.com/pyobs/pyobs-gui/pull/155).
6. ~~Tests: state round-trip, publish transitions, schedule trimming, `get_schedule` cap.~~ Done
   both sides — pyobs-core half in #826; pyobs-gui half (`tests/test_roboticwidget.py`,
   `tests/test_schedulewidget.py`, a `FakeComm` pattern rather than
   `test_mainwindow_startup.py`'s) in #155.
