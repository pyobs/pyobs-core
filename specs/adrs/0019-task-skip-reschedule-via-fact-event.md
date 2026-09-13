# Task-skip reschedule trigger: a fact event, not a command or new interface method

status: accepted
date: 2026-09-10

## Context and Problem Statement

When `Mastermind` skips a scheduled task because its start window was missed by more than
`allowed_late_start` (issue pyobs-core#895), something needs to tell the `Scheduler` module to
recompute — otherwise the stale, unrunnable observation just keeps being returned by
`get_next_observation()` until it ages out on its own. `Mastermind` and `Scheduler` are separate
modules communicating only over the comm layer, so the question is which mechanism carries that
"recompute now" trigger across the module boundary.

## Considered Options

* **`Mastermind` calls `IRunnable.run()` on the scheduler via `self.safe_proxy(...)`.** Works and
  needs no new event, but requires `Mastermind` to know the scheduler's module name/JID (a new
  config field) and couples the executor to the planner; a mastermind configured without it
  silently loses the behavior.
* **A new `reschedule()` method on `IRoboticScheduler`/`ObservationArchive`.** `IRunnable.run()`
  already is that method, and `specs/design/irobotic.md` explicitly keeps re-scheduling on it
  ("no new method").
* **A command-style event** (`RescheduleEvent`, `RescheduleRequestEvent`) sent by `Mastermind` and
  acted on unconditionally by `Scheduler`. Reads as an instruction from one module to another
  (or as something that fires *after* a reschedule already happened), which breaks the
  fact/handler convention below and still implicitly assumes a scheduler is listening.
* **A fact event** (`TaskSkippedEvent`), reporting only that a scheduled task was skipped and why;
  `Scheduler._on_task_skipped` independently decides that means "recompute" (chosen).

## Decision Outcome

Chosen option: **a fact event**, `TaskSkippedEvent(name, id, reason)`, modeled on the existing
`TaskFailedEvent`. pyobs events already report facts while handlers own the policy that follows —
`GoodWeatherEvent` → `Scheduler._on_good_weather` and `TaskFinishedEvent` →
`Scheduler._on_task_finished` both just observe an event and independently decide to reschedule.
`TaskSkippedEvent` follows the same shape: `Mastermind` reports *this scheduled task was skipped*,
and stays completely ignorant of whether a scheduler exists, what it's called, or that a
reschedule is the remedy. A deployment with no scheduler on the comm bus simply ignores the event
and behaves exactly as before this change.

## Consequences

* `Mastermind` needs no scheduler reference or config field; the coupling lives entirely in
  `Scheduler._on_task_skipped` (`pyobs/modules/robotic/scheduler.py`), which is free to change how
  it reacts (e.g. add throttling) without touching `Mastermind`.
* Any future skip cause (not just late-start) can reuse `TaskSkippedEvent` with a different
  `reason` instead of growing a new event type per cause.
* Because the event carries no scheduler-specific semantics, a persistently-recurring skip (e.g. a
  chronically overrunning predecessor task) reschedules on every occurrence unless the handler
  itself adds a cooldown — the event's fact-only design pushes that responsibility to the handler,
  not the sender.
