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
- `cant_run_reason` must be computed fresh at publish time from the *current* `next`
  observation (`self._task_runner.cant_run_reason(next.task)` if `next` is not `None`, else
  `None`). It must **not** be read off `Mastermind._last_cant_run_reason` — that field is a
  `dict[task_id, str]` used only to dedupe repeated log lines in `_run_thread`, keyed by
  whichever tasks have recently failed `can_run()`; entries for tasks that stop being "next"
  are never cleared, so it can hold several stale reasons at once and has no defined mapping
  to a single scalar.
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
state on `open()`, `start()`, `stop()`, and on every task transition in `_run_thread`
(started / finished / failed):

- `current` ← `self._task`, `self._task_target`, `self._obsnum` (+ ETA from `task.duration`);
  already in memory, no extra query.
- `next` ← `self._observation_archive.get_next_observation(now, self._task_archive)` — **not**
  free: for `LcoObservationArchive` this is a live portal HTTP call. Only call it from inside
  `_run_thread`, where it already runs every loop iteration regardless; never re-derive it on
  an RPC path (there is no `get_status()` — see above).
- `cant_run_reason` ← computed at publish time as `self._task_runner.cant_run_reason(next.task)`
  if `next` is not `None`, else `None`. Do not read `self._last_cant_run_reason` for this —
  it's a private log-dedup cache (`dict[task_id, str]`), not a snapshot of "why can't the next
  task run right now".

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

Data flow: `subscribe_state(module, <interface>, ...)` for steady state — a new subscriber
gets the last-pushed value immediately, so this also covers initial load / refresh, no
separate pull RPC needed — `register_event(TaskStartedEvent/TaskFinishedEvent/TaskFailedEvent)`
for instant updates, proxy calls for `start` / `stop` / `get_schedule` / `run`. Buttons gated by
ACLs via `self.permitted(...)` (see `pyobs-gui/specs/plans/2026-07-29-gui-acl-aware-widget-gating.md`).

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

1. Interface files + exports + dataclass serialization (round-trip tests).
2. `Mastermind` state publishing (transitions in `_run_thread`, `cant_run_reason` derived fresh
   from `next` at publish time — not from `_last_cant_run_reason`).
3. `Scheduler` state publishing and `get_schedule` trimming + hard server-side cap.
4. Add `obsnum: str | None` to `TaskStartedEvent` / `TaskFinishedEvent` / `TaskFailedEvent`.
5. `RoboticWidget` + `ScheduleWidget` implementations and `DEFAULT_WIDGETS` registration.
6. Tests: state round-trip, publish transitions, schedule trimming, `get_schedule` cap; GUI
   fake-comm tests per `pyobs-gui/tests/test_mainwindow_startup.py` patterns.
