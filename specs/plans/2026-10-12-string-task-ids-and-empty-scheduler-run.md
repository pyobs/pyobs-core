# Scheduler: string task ids from the portal and the empty-task crash

Status: implemented (PR #955), released in v2.15.0.

Repos: pyobs-core

## Context

Reported externally by MichaelJEvan on a second site (pyobs-core 2.14.2, pyobs-portal 2.5.5):
#952 items 1 and 2, and #953. All three were checked against `develop` (`0f64f50a`) and are
still present.

Portal task ids and the `Observation.task` of observations from the portal archive are plain
strings, while parts of the robotic code assume integer ids or a full `Task` object. Three
places break:

1. **`scheduler.py:233`**: `log.info("... ID %d ...", removed[0], ...)` with a string id. Stdlib
   logging alone only prints "Logging error", but `CommLoggingHandler.emit` (`commlogging.py:37`)
   calls `Formatter.format()` outside a try block, so the `TypeError` escapes `log.info`.
   `_update_schedule` aborts before `self._tasks = tasks`, the removal is never seen, and the
   scheduler keeps planning the deactivated task on every trigger (1235 and 1372 pending
   observations on two nights). The portal poll also logs the format error as a failed update.
2. **`ondemandscheduler.py:325`**: `np.argmax(merits)` on an empty list raises `ValueError`
   when there are no schedulable tasks. Every run against an empty portal ends in "Something
   went wrong".
3. **`observation.py:120`** (#953): `ObservationList.filter(task_id=...)` reads `obs.task.id`,
   but the portal archive returns `task` as the plain task code (see the comment in
   `storage/portal/observationarchive.py:87`; `Observation.task` is typed `Task | Any`).
   `FollowMerit` (`merits/follow.py:29`) therefore raises `AttributeError: 'str' object has no
   attribute 'id'` as soon as the night has one COMPLETED observation, and nothing is planned.

## Proposed changes

1. `scheduler.py:233`: `%d` becomes `%s`. Same check for every other log format string that
   takes a task or observation id (only this one found so far, line 230 and 373 use counts).
2. `OnDemandScheduler.find_next_best_task`: return `(None, 0.0)` if `tasks` is empty, before
   evaluating the merits.
3. Add a helper on `Observation`, e.g. `task_id` property, returning `self.task.id` if `task`
   is a `Task`, else `self.task`. Use it in:
   - `ObservationList.filter()` (the actual #953 fix),
   - `Observation.__eq__` / `__ne__` and `__str__` (same `self.task.id` / `self.task.name`
     assumption, `__str__` also reads `.name`), so equality and logging do not hit the same
     `AttributeError` for unresolved observations.

## Tests

- Scheduler: removal of a task with a string id runs through `_update_schedule` with
  `CommLoggingHandler` attached (or `logging.raiseExceptions` semantics reproduced) and updates
  `self._tasks`.
- `OnDemandScheduler.find_next_best_task([])` returns `(None, 0.0)`.
- `ObservationList.filter(task_id=...)` with observations whose `task` is a `Task` and with
  observations whose `task` is a string.
- `FollowMerit` returns 1.0 with a completed observation carrying a string task.
- `Observation.__eq__` and `__str__` with a string `task`.

## Decisions

- `filter(task_id)` is typed `Any` and compares as given (ids are mostly `str` or `int`).
- `Observation.__str__` prints `#<id>` only when `task` is not a `Task`.

## Out of scope

The XMPP findings of #952 (items 3 to 8) are a separate plan: items 3 and 5 share a cause
(a failed disco#info is treated as "no interfaces" and then acted on or cached).
