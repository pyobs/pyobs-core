# Plan: reschedule on project and same-ID task content changes

Status: proposed

Tracks issue #848. Repos: pyobs-core (this plan); the signal-delivery half lives in
`pyobs-portal/specs/plans/2026-09-01-last-task-update-marker-includes-projects.md` (separate
repo, separate plan) — the two are independently landable, see Out of scope.

## Problem

`Scheduler._update_schedule()` (`pyobs/modules/robotic/scheduler.py:174-228`) downloads both
tasks and projects every time `on_tasks_changed` fires, but its `_need_update` gate is driven
entirely by `_compare_task_lists()` (`:231-252`), which diffs **task IDs only**:

- Projects are downloaded (`:184`) and stored, but never compared against the previous
  download. A project's `priority` (multiplied into every task's merit in
  `evaluate_constraints_and_merits()`, `pyobs/robotic/scheduler/ondemandscheduler.py:247-250`)
  can change with the task-ID set completely unchanged, and `_need_update` stays `False`
  ("No change in list of blocks detected.").
- A task whose own content changed (priority, duration, script) but whose `id` didn't is
  likewise invisible to `_compare_task_lists` — it's neither `removed` nor `added`.

Confirmed while investigating: `self._projects = await self._task_archive.get_projects()`
(`:184`) overwrites the cached list **before** any comparison could happen — unlike
`self._tasks = tasks`, which is correctly deferred to the end of the method (`:221`) so the old
value survives long enough to diff against. Any project-diff fix has to fix this ordering first,
or it will always compare a list against itself.

`PortalTaskArchive._update()` (`pyobs/robotic/storage/portal/taskarchive.py:92-102`) already
solves the identical problem one layer down — it fires `_on_tasks_changed` only when
`{p.code: p.model_dump()}` or `{t.id: t.model_dump()}` actually differ from the cached copy —
so the comparison shape here isn't new design, it's the same pattern one level up.

## Design

### 1. Fix the assignment-order bug

In `_update_schedule()`, download projects into a local variable and keep `self._projects`
(old) around until the comparison runs; reassign both `self._tasks` and `self._projects` at the
end (`:221`), the same place `self._tasks = tasks` already happens.

### 2. Project content-diff

- Compare `{p.code: p.model_dump() for p in old_projects}` against
  `{p.code: p.model_dump() for p in new_projects}` — same shape as
  `PortalTaskArchive._update()` (`taskarchive.py:96-98`).
- Extend the "no changes" gate (`:193`, currently `len(removed) == 0 and len(added) == 0`) to
  also require `not projects_changed`.
- No other change needed: because `removed`/`added` stay empty when only a project changed, the
  two downgrade checks that follow — "removed == only the currently-running task" (`:207`) and
  "none of the removed tasks were actually scheduled" (`:213`) — are both gated on
  `len(removed) > 0`/`len(removed) == 1`, so they never fire and `_need_update` stays `True`
  straight through.

### 3. Task content-diff (same ID, different content)

- Add a new comparison alongside the existing ID-only `_compare_task_lists()`: for IDs present
  in both the old and new task lists, `changed_ids = {id for id in common_ids if
  old_by_id[id].model_dump() != new_by_id[id].model_dump()}`. Keep this as a separate helper
  (e.g. `_diff_task_content()`) rather than folding it into `_compare_task_lists`, which is a
  `@staticmethod` with an existing, narrowly-scoped removed/added contract used only for the two
  downgrade checks above — content-diff is a different axis and conflating them risks breaking
  those checks' assumptions.
- `changed_ids` also holds off the "no changes" downgrade, same as `projects_changed`.
- **New asymmetry vs. removed/added, worth calling out explicitly**: a *removed* currently-running
  task is deliberately not rescheduled around (`:207` — it's ending anyway), but a *changed*
  currently-running task (`changed_ids == {self._current_task_id}`) should still force a
  reschedule — a live priority bump on the running task can reorder everything scheduled after
  it. Do not reuse the `:207` downgrade for `changed_ids`.
- Do reuse the schedule-membership guard (`:213`'s pattern): if none of `changed_ids` are
  actually present in `await self._schedule.get_schedule()`, a content change to a task that
  isn't on the current schedule can't affect the active plan — skip, same reasoning as the
  existing removed-from-schedule check.
- `model_dump()`-based comparison depends on `Task`'s runtime/mutable state living only in
  `PrivateAttr`s (`_cant_run_reason`, `_resolved_target`, `_running_script` —
  `pyobs/robotic/task.py:53-55`), which `model_dump()` excludes by construction. This matters
  more here than in `PortalTaskArchive`: `self._tasks` here are the *exact* objects handed to
  `self._scheduler.schedule(self._tasks, self._projects, ...)` (`scheduler.py:286`) on every
  run, so anything the scheduler mutates on them via `resolve_target()`/`can_run()` must stay
  confined to private attrs for this comparison to stay stable. Verified for current code (no
  declared field, e.g. a resolved `Target.name`, is set directly during scheduling) but add a
  regression test for it explicitly rather than relying on re-reading the scheduler's internals
  next time it changes.

### Tests (`tests/modules/robotic/test_scheduler.py`)

- Project-only content change (priority bump; also `users` and `public`), task list otherwise
  identical → `_need_update` True.
- Same-ID task content change, task not present in the current schedule → `_need_update` stays
  False (schedule-membership guard).
- Same-ID task content change, task present in the current schedule, not the running task →
  True.
- Same-ID task content change on the currently-running task → True (the asymmetry above).
- Regression: run a task through `self._scheduler.schedule(...)` (or call
  `resolve_target()`/`can_run()` directly on it) and diff it against a freshly-downloaded,
  otherwise-identical copy — must compare equal (guards the private-attr mutation risk above).

## Acceptance criteria

- [ ] Project-only content change triggers a reschedule.
- [ ] Assignment-order bug fixed — old projects are diffed against new before `self._projects`
      is overwritten.
- [ ] Same-ID task content change triggers a reschedule when the task is on the current schedule
      or is the running task; is skipped when the task isn't on the schedule at all.
- [ ] Existing `_compare_task_lists` contract and its two removed/added downgrade checks are
      unchanged for pure add/remove cases — no regression in current scheduler tests.
- [ ] New tests listed above pass.
- [ ] `ruff`/`pyrefly` clean.

## Out of scope

- pyobs-portal's `/api/last_task_update/` marker not moving on project edits — a separate,
  required gap for the fix to matter in production (without it, `PortalTaskArchive` never
  re-polls, so this plan's comparison never even runs on a real project edit). Tracked in
  `pyobs-portal/specs/plans/2026-09-01-last-task-update-marker-includes-projects.md`. The two
  plans are independently correct and independently landable — this one is already exercised by
  `trigger_on_every_update=True` deployments and by the new tests regardless of portal state.
