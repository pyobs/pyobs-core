# Plan: Mastermind triggers a reschedule when a start window is skipped for lateness (pyobs-core#895)

Status: implemented, pending PR (branch `895-mastermind-reschedule-on-late-skip`) (Repos: pyobs-core)

Issue: pyobs-core#895

Implemented as written below: `TaskSkippedEvent` + export, `Mastermind` emission gated on the
skipped observation's identity (via a new `Mastermind._same_observation()` helper, also reused by
`_track_next_observation`), and `Scheduler._on_task_skipped` registered in `open()`. Tests pass;
`ruff`, `black`, and `pyrefly` are clean (full standalone suite: 1927 passed, 23 pre-existing
environmental failures unrelated to this change — astropy IERS offline / read-only cache paths).

## Problem

`Mastermind._run_thread` (`pyobs/modules/robotic/mastermind.py:224-243`) polls
`ObservationArchive.get_next_observation()` every 10s. When an observation is scheduled but its
`start` is more than `allowed_late_start` in the past (and `task.can_start_late` is false), the loop
warns once, keeps the skipped observation visible as `next`, sleeps, and re-polls:

```
2026-09-09 16:44:33 [WARNING] [localhost] (mastermind) mastermind.py:230 Time since start of window (1119.1) too long (>300.0), skipping task...
```

Nothing asks the scheduler to recompute. The skipped entry stays `PENDING` in the
`ObservationArchive`, so `get_next_observation()` keeps returning it until `now >= observation.end`;
only then does it age out, and the mastermind silently advances to the next schedule entry — itself
possibly computed against the assumption that the skipped task ran. The plan is never re-derived
around the miss.

## Investigation: the reschedule hook

The issue left open "what reschedule hook is available on `TaskArchive`/`self._task_archive`".
Answer: none, and it doesn't need one.

- `TaskArchive` (`pyobs/robotic/storage/taskarchive.py`) exposes `last_changed()`,
  `get_projects()`, `get_schedulable_tasks()`, `get_task()`, `get_instrument_capabilities()`, and
  the `on_tasks_changed` callback. The callback only fires from the archive's own poller (e.g.
  `PortalTaskArchive._update()`, `lco/taskarchive.py:70`); nothing can poke it from outside.
- The hook is the **`Scheduler` module's `run()`** (`pyobs/modules/robotic/scheduler.py:405`,
  inherited from `IRunnable`): it sets `_need_update = True`, which `_schedule_worker` picks up on
  its next 1s tick and turns into a full `clear_schedule(start)` + reschedule. This is already the
  documented "reschedule now" path (`docs/source/recipes/robotic.rst` and
  `docs/source/api/robotic/index.rst` → "Scheduler re-triggering").
- The existing automatic triggers don't cover this case: `trigger_on_task_started` /
  `trigger_on_task_finished` both default to `False`, and a *skipped* task emits neither
  `TaskStartedEvent` nor `TaskFinishedEvent`.

## Design

### A fact event, not a command

pyobs events report facts; handlers own the policy that follows. `GoodWeatherEvent` →
`Scheduler._on_good_weather` (`scheduler.py:495`) and `TaskFinishedEvent` → `_on_task_finished`
(`scheduler.py:471`) both just set `_need_update` / `_schedule_start`. So the new event reports
what happened — *this scheduled task was skipped* — and the scheduler independently decides that
means "recompute".

This keeps `Mastermind` ignorant of the planner: it never has to know a scheduler exists, its
module name, or that a reschedule is the remedy. A deployment with no scheduler on the comm simply
ignores the event, i.e. behaves exactly as today.

Deliberately **not** named `RescheduleEvent` / `RescheduleRequestEvent`: those read as a command,
and/or as an event that fires *after* a reschedule, both of which break the convention above.

### `TaskSkippedEvent` (`pyobs/events/taskskipped.py`)

Modeled on `TaskFailedEvent`:

```python
class DataType(TypedDict):
    name: str
    id: Any
    reason: str


class TaskSkippedEvent(Event):
    """Event to be sent when a scheduled task is skipped without running."""

    __module__ = "pyobs.events"

    def __init__(self, name: str, id: Any, reason: str, **kwargs: Any): ...
    # read-only properties: name, id, reason
```

- Export from `pyobs/events/__init__.py` (import + `__all__`). `EventFactory.from_dict()`
  (`pyobs/events/event.py`) resolves the class by looking the type name up on the `pyobs.events`
  package, so the export is what makes it deserializable on the receiving side.
- No custom `from_dict()`: every field is JSON-native, so the base `Event.from_dict()`'s
  `cls(**data)` handles it — same as `TaskFailedEvent`.
- `reason` is a free-form human-readable string, consistent with `RoboticState.cant_run_reason`'s
  existing free-form treatment. `Mastermind` passes a fixed literal; promote to an enum only if a
  second skip cause ever appears.

### `Mastermind`: emit once per distinct stale observation

The current one-shot gate is a local `first_late_start_warning` bool (`mastermind.py:187`,
`:229-235`, reset at `:245-246`). It is reset only when a task *actually starts*, so two different
stale observations in a row produce only one warning — and, with this change, only one reschedule.
Gate on the skipped observation's identity instead (the same `task.id`/`start`/`end` fields
`_track_next_observation()` already compares, now factored into a small
`Mastermind._same_observation(a, b)` static helper and reused by both):

```python
late_skipped: Observation | None = None
...
if late_start > self._allowed_late_start * u.second:
    if late_skipped is None or not self._same_observation(late_skipped, observation):
        log.warning(
            "Time since start of window (%.1f) too long (>%.1f), skipping task...",
            late_start.to_value("second"),
            self._allowed_late_start,
        )
        await self.comm.send_event(
            TaskSkippedEvent(
                name=observation.task.name,
                id=observation.task.id,
                reason=f"start window missed by {late_start.to_value('second'):.0f}s",
            )
        )
        late_skipped = observation

    # keep the skipped observation visible as `next` rather than leaving
    # whatever was last published stale for as long as this repeats
    await self._track_next_observation(observation, None)
    await asyncio.sleep(10)
    continue
```

- `first_late_start_warning` and its reset at `:245-246` are removed; the identity gate subsumes
  both.
- `Mastermind.open()` additionally calls `await self.comm.register_event(TaskSkippedEvent)`
  (no handler — registration is what permits `send_event`, mirroring the existing
  `TaskStartedEvent` / `TaskFinishedEvent` registrations at `mastermind.py:119-120`).
- The event is sent once per distinct stale observation, not once per 10s loop iteration.
- Clearing `late_skipped` is unnecessary: a scheduler recompute is driven from `Time.now()`, so a
  re-scheduled observation of the same task gets a new `start`/`end` and therefore re-emits. The
  only case that would suppress a re-emit is a scheduler re-adding an *identical, already-expired*
  window, which would be a scheduler bug rather than something this gate should paper over.

### `Scheduler`: `_on_task_skipped`

Register in `Scheduler.open()` alongside the existing subscriptions (`scheduler.py:162-165`) and
add, next to the other handlers:

```python
async def _on_task_skipped(self, event: Event, sender: str) -> bool:
    """Re-schedule when a task's start window was skipped as too late.

    Args:
        event: The task skipped event.
        sender: Who sent it.
    """
    if not isinstance(event, TaskSkippedEvent):
        return False

    log.info("Received task skipped event (%s), triggering new scheduler run...", event.reason)
    self._need_update = True
    self._schedule_start = Time.now()
    return True
```

- **Unconditional**, not behind a `trigger_on_task_skipped` flag like the started/finished
  handlers, matching `_on_good_weather`: the event only ever fires when a window was actually lost
  and the remedy is always a recompute, so a flag would add config surface with no real choice
  behind it.
- `_schedule_start = Time.now()` mirrors `_on_task_finished`; `_schedule_worker` already lifts a
  too-soon start to `now + safety_time`.
- The triggered reschedule's `clear_schedule(start)` drops still-`PENDING` schedule entries whose
  `end` is after the new start (typically the skipped observation itself, whose window is still
  open), so it stops being re-returned by `get_next_observation()`. An entry whose `end` has
  already passed simply ages out as it does today.

## Alternatives considered

- **`Mastermind` calls `IRunnable.run()` on the scheduler via `self.safe_proxy(...)`.** Works and
  needs no new event, but requires `Mastermind` to know the scheduler's module name/JID (a new
  config field) and couples the executor to the planner; a mastermind configured without it
  silently loses the behavior. Rejected in favor of the event.
- **A new `reschedule()` method on `IRoboticScheduler`/`ObservationArchive`.** `IRunnable.run()`
  already is that method, and `specs/design/irobotic.md` explicitly keeps re-scheduling on it
  ("no new method"). Rejected.
- **Command-style event (`RescheduleEvent`, `RescheduleRequestEvent`).** Rejected — see naming
  rationale above.

## Behavior changes

- The late-start warning now fires once per *distinct* stale observation instead of once per stuck
  episode (the old global bool never reset when the schedule went empty). That is what the event
  gating requires, and it also makes the warning honest about which window it refers to.
- No new config, no interface change, no event protocol version bump.

## Non-goals

- **Mastermind-side schedule mutation** — marking the skipped observation
  `WINDOW_EXPIRED`/`CANCELED` from `Mastermind`. The scheduler's `clear_schedule()` already removes
  it on recompute, and the portal's own `mark_window_expired` sweep owns the server-side state;
  keeping `Mastermind` out of the archive keeps a single writer for schedule state.
- **Rescheduling on other skip causes** — this event covers only the late-start skip. A future
  "cannot run for N minutes" trigger would reuse `TaskSkippedEvent` with a different `reason`.
- **Changing the 10s poll interval or the `allowed_late_start` default.**

## Testing

- `tests/test_events.py`: `TaskSkippedEvent` properties + `EventFactory` round-trip, following the
  per-event `test_*_properties` / `test_*_roundtrip` block already there.
- `tests/modules/robotic/test_scheduler.py`: `_on_task_skipped` ignores a wrong event type; sets
  `_need_update` / `_schedule_start` (≈ `Time.now()`) on a real `TaskSkippedEvent`; `open()`
  registers the event.
- `tests/modules/robotic/test_mastermind.py`: drive `_run_thread` with the
  `fake_sleep`-raises-`CancelledError` pattern already used in `test_dummymastermind.py`, with a
  mocked `get_next_observation()` returning an observation whose `start` is well past
  `allowed_late_start` and `can_run()` returning `True`:
  - exactly one `TaskSkippedEvent` is sent across several loop iterations for the same
    observation;
  - a second, distinct stale observation produces a second event;
  - no event when the task isn't late, or when `can_start_late` is true.

## Docs

- `docs/source/api/events.rst`: add `TaskSkippedEvent` to the autoclass list (alphabetically
  between `TaskFinishedEvent` and `TaskStartedEvent`).
- `docs/source/api/robotic/index.rst` → "Scheduler re-triggering": add a bullet for the new event.
- `docs/source/recipes/robotic.rst`: the "call the scheduler's `run` method … to trigger an
  immediate reschedule" note stays (still the manual path), with a sentence that a late-skipped
  window now triggers it automatically.
- Optional: `specs/design/irobotic.md` (proposed, #825) — note the skip → reschedule event on the
  `Mastermind` / `Scheduler` sections.

## Rollout

Pure `pyobs-core` change: one new event class, one send site, one handler registration. Backward
compatible in both directions — an older scheduler ignores the unknown event; a newer scheduler
with an older mastermind simply never receives it and behaves as today (manual `run()` still
works). Rollback is reverting the event, the send, and the handler registration.
