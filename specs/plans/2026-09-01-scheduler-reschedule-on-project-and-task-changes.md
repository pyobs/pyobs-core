# Plan: reschedule on project and same-ID task content changes

Status: implemented

Tracks issue #848. Repos: pyobs-core (this plan); the signal-delivery half lives in
`pyobs-portal/specs/plans/2026-09-01-last-task-update-marker-includes-projects.md` (separate
repo, separate plan). **Not independently landable** — see Out of scope: pyobs-portal's
`Project` payload gained `updated_at`, which core's `Project` model must accept a round-trip
field for (added in this PR) or every poll fails with a `ValidationError`.

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

- [x] Project-only content change triggers a reschedule.
- [x] Assignment-order bug fixed — old projects are diffed against new before `self._projects`
      is overwritten.
- [x] Same-ID task content change triggers a reschedule when the task is on the current schedule
      or is the running task; is skipped when the task isn't on the schedule at all.
- [x] Existing `_compare_task_lists` contract and its two removed/added downgrade checks are
      unchanged for pure add/remove cases — no regression in current scheduler tests.
- [x] New tests listed above pass (implemented as `_changed_task_ids()` rather than the
      originally-sketched `_diff_task_content()` name; behavior matches).
- [x] `ruff`/`pyrefly` clean. Full non-integration suite (1786 tests) also green.

## Out of scope

- pyobs-portal's `/api/last_task_update/` marker not moving on project edits — a separate,
  required gap for the fix to matter in production (without it, `PortalTaskArchive` never
  re-polls, so this plan's comparison never even runs on a real project edit). Tracked in
  `pyobs-portal/specs/plans/2026-09-01-last-task-update-marker-includes-projects.md`.

## Post-review addendum

Independent review of the initial implementation (verified against PR head `a374458d`) found
and this PR's follow-up commit fixed:

- **Coupling, not independence**: pyobs-portal's `ProjectSerializer` is `fields="__all__"`, so
  once pyobs-portal#134 lands, `/api/projects/` starts emitting `updated_at`. Core's `Project`
  (`pyobs/robotic/task.py:152`) is `extra="forbid"` with no such field, so
  `PortalTaskArchive._get_projects()` (`taskarchive.py:117`) would raise `ValidationError` on
  every poll — the two PRs are **not** independently landable as originally claimed. Fixed by
  adding `updated_at: str | None = None` to `Project`, mirroring the identical precedent already
  shipped for `Task.updated_at` (commit `e550423e`, pyobs-portal#84), plus a regression test
  (`test_task_get_projects_from_portal_accepts_updated_at`) mirroring that precedent's own test.
- **`updated_at` leaking into content comparisons**: once `Project` carries `updated_at`, both
  `projects_changed` and `_changed_task_ids()`'s `model_dump()` comparisons would count a no-op
  re-save (timestamp-only change) as a real content change, forcing spurious reschedules. Fixed
  by excluding `updated_at` from both comparisons. For `Task` this could **not** be done via
  `model_dump(exclude={"updated_at"})`: `Task` is a `PolymorphicBaseModel`, whose
  `@model_serializer` (`pyobs/utils/serialization.py:44-49`) builds its own dict from
  `model_fields` via `getattr` and never calls `handler(self)`, so it silently ignores
  `exclude`/`include` entirely — filed as a separate, wider-scoped follow-up,
  pyobs-core#855. Worked around locally with `Scheduler._content_dump()`, which dumps
  normally and pops the key from the resulting dict.
- **Regression test breadth**: `test_changed_task_ids_ignores_private_attr_mutation` now also
  sets `_resolved_target`/`_running_script`, not just `_cant_run_reason`, guarding all three
  `PrivateAttr`s a real scheduling round-trip can touch.
- **Missing coverage** (nits): added `test_update_schedule_project_removed_triggers_update` and
  a mixed removed+changed poll test (the currently-running task removed at the same time as an
  unrelated task's content changes — the latter must still force a reschedule).

## Merge-conflict addendum (rebase onto develop)

While rebasing onto `develop`, PR #852 (issue #847, landed concurrently) turned out to conflict
at the design level, not just textually: it **deleted** the "was one of the removed tasks
actually in `self._schedule.get_schedule()`?" guard this plan's design (§3) explicitly said to
*reuse* for `changed_ids`. Their reasoning: `PortalObservationArchive`'s schedule cache is
permanently empty by construction (the `Scheduler` runs it with `auto_update=False`), so that
guard always found nothing and silently discarded every real portal task removal — the exact bug
#847 fixed. Reusing the same guard for `changed_ids` would have reintroduced the identical bug
one level up: every same-ID content change to a task would have been silently swallowed on a
portal deployment, defeating the entire point of #848.

Resolution: dropped the schedule-membership guard for `changed_ids` too (never added it back),
matching #852's decision. Net effect: a project change, a task removal, a task addition, or a
same-ID task content change all now force a reschedule unconditionally (modulo the one remaining
downgrade — a removal that's exactly the currently-running task ending on its own, and only
that). This *simplifies* the design in §3: the "asymmetry" between a removed vs. changed running
task, and the `current_task_changed` bypass variable, are no longer needed — with no membership
check left to bypass, a changed running task simply flows through as `True` like everything else.
Rewrote the affected tests to match (no longer mocking/asserting on `get_schedule()` for content
changes, mirroring #852's own `..._without_consulting_schedule_cache` naming).
