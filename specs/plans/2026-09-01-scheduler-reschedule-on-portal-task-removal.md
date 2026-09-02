# Plan: Reschedule on portal task removal instead of gating on an empty schedule cache

Status: implemented (PR #852; part 2 revised in review — see below)
Repos: pyobs-core
Issue: pyobs-core#847

## Problem

When a task is deactivated (`active=false`) or deleted in pyobs-portal while it has pending
observations, the scheduler never reschedules and the mastermind gets stuck logging
`Could not resolve task for observation N, skipping.` every ~10 s until the observation's window
passes on its own. The freed slot is never refilled; the stale observation stays pending in the
portal.

Root cause chain (from #847):

1. Portal's `/api/tasks/` filters `active=True`, so a deactivated task disappears from
   `PortalTaskArchive`'s next poll.
2. `PortalTaskArchive` fires `on_tasks_changed` → `Scheduler._update_schedule()`
   (`pyobs/modules/robotic/scheduler.py:174`).
3. `_update_schedule()` gates rescheduling on "was the removed task actually in the computed
   schedule?" (`scheduler.py:213-218`), checked via `self._schedule.get_schedule()`. For
   `PortalObservationArchive` that method just returns `self._observations`
   (`observationarchive.py:162-172`), which is **permanently empty** here: the scheduler
   constructs this archive with `auto_update=False` (`scheduler.py:114-115`) specifically to stop
   its own background poller from double-driving updates, but that also means nothing ever
   populates `_observations`. So `removed_from_schedule` is always `[]` → the gate always fires →
   `_need_update = False` → no reschedule, unconditionally, for every task removal on a portal
   deployment.
4. Deactivation doesn't cascade to observations (separate pyobs-portal issue, out of scope here),
   so the mastermind's `PortalObservationArchive.get_next_observation()` /
   `get_current_observation()` keep finding the same stale `pending` observation, calling
   `fetch_task()` on it, getting `None` back from `PortalTaskArchive.get_task()` (the task is
   gone from the cached active list), and logging-and-skipping on every poll
   (`observationarchive.py:184-193`, `195-215`).

## Design

### 1. Scheduler: drop the "was it scheduled?" gate (required — this is the actual bug)

`removed_from_schedule = [s for s in schedule if s.task.id in removed]` (`scheduler.py:215`) was
added in `b3464f89` (2022) purely as an optimization to skip pointless reschedule runs, predating
the portal archives. It was never a correctness requirement, and for `PortalObservationArchive`
it is unconditionally wrong (empty cache by construction — see above), not just occasionally
wrong. It's also independently buggy: `PortalObservationArchive` observations can carry `task` as
a bare int FK before `fetch_task()` resolves it (same pattern guarded in
`pyobs/robotic/storage/lco/observationarchive.py:99`), so `s.task.id` is a latent
`AttributeError` regardless of the empty-cache issue.

Remove the check. Reschedule on any removal except the one case that's a real, cheap-to-detect
no-op: the single removed task is the currently-running one (`scheduler.py:207-210`, unchanged).

```python
# scheduler.py, _update_schedule() — delete this block entirely:
#
# # check, if one of the removed blocks was actually in schedule
# if len(removed) > 0 and self._need_update:
#     schedule = await self._schedule.get_schedule()
#     removed_from_schedule = [s for s in schedule if s.task.id in removed]
#     if len(removed_from_schedule) == 0:
#         log.info("Found %s tasks, but none of them was scheduled.", len(removed))
#         self._need_update = False
```

No replacement logic — the existing "only the currently-running task was removed" check
(`removed[0] == self._last_task_id`) already covers the one case worth special-casing. Trade-off:
occasional extra reschedule runs for archives (e.g. LCO) where `get_schedule()` is actually
populated and the removed task genuinely wasn't scheduled. Accepted — the module already exposes
`trigger_on_every_update` for "reschedule aggressively," so erring toward more reschedules is
consistent with this module's existing design, and a spurious reschedule is a bounded-cost bug
while a missed one wedges the mastermind indefinitely.

### 2. Mastermind / PortalObservationArchive: self-heal on unresolvable task (defense-in-depth)

Even after (1), a window between "task removed from portal" and "scheduler reschedule completes
and republishes a clean schedule" can still leave an orphaned observation with `task is None`
after `fetch_task()`. Rather than log-and-skip it forever every poll, mark it `CANCELED` so it
drops out of the pending set immediately, both locally and on the portal.

`get_task()` returning `None` is a safe signal to act on: `PortalTaskArchive.get_task()`
(`pyobs/robotic/storage/portal/taskarchive.py:148-158`) is a pure in-memory lookup against the
last successfully-polled task list — it never raises on network errors (those are caught in the
background poller and leave the last-known-good list in place), so `None` means "genuinely not in
the current active list," not "transient hiccup."

In `PortalObservationArchive` (`observationarchive.py`), add `_resolve_or_cancel_pending()`, used
only from `get_next_observation()`'s pending-observation path (**not** `get_current_observation()`
— see revision below):

```python
async def _resolve_or_cancel_pending(self, obs: Observation, task_archive: TaskArchive) -> bool:
    """Resolve a pending obs.task; if the task archive has polled at least once and the portal
    no longer has the task, mark obs canceled so it stops being retried. Returns True if obs is
    usable."""
    task_id = obs.task
    await obs.fetch_task(task_archive)
    if obs.task is not None:
        return True
    if await task_archive.last_changed() is None:
        log.error("Could not resolve task for observation %s, skipping.", obs.id)
        return False
    log.error("Could not resolve task for observation %s, marking canceled.", obs.id)
    obs.task = task_id  # portal's task FK is non-nullable -- keep the id for the PUT payload
    obs.state = ObservationState.CANCELED
    try:
        await self.update_observation(obs)
    except Exception as e:
        log.error("Failed to mark observation %s canceled on portal: %s", obs.id, e)
    return False
```

Mutating `obs.state` in place (not just the remote PUT) matters: `self._observations` is the same
list `get_next_observation()` iterates, so without the local mutation the same observation gets
re-fetched-and-relogged on every call within the same poll cycle, not just every 10 s poll.

Swallow (log, don't raise) a failed `update_observation()` PUT — a portal hiccup here shouldn't
crash the mastermind's poll loop; state will resync on the next successful update.

**Revision from review (before merge):** the initial draft of this section had three bugs, all
caught in PR #852's review and fixed before merge:

1. **Cancel payload never persisted.** `obs.fetch_task()` leaves `obs.task = None` on a miss;
   `update_observation()` → `model_dump(use_task_id=True)` only overrides `data["task"]` when
   `isinstance(self.task, Task)` (`observation.py:86`), so with `task=None` it serialized the raw
   field — `task: null`. The portal's `Observation.task` FK is non-nullable, so the PUT was
   rejected every time; the exception was caught and logged as designed, but the cancel never
   landed, and the escape hatch this plan originally cited ("the observation will also disappear
   from the next `_get_schedule()` fetch regardless") doesn't hold either — the portal's
   observation filter is state/time-only, not task-activity-aware, and deactivation doesn't
   cascade. Net effect: a *permanent*, now double-noisy (two ERROR lines/poll), failed-cancel
   loop. Fixed by saving `obs.task` before calling `fetch_task()` and restoring it onto `obs`
   before building the cancel payload.
2. **Startup race could wrongfully cancel.** `PortalTaskArchive.get_task()` returns `None` both
   for "genuinely not in the active list" and for "task archive has never completed a poll yet"
   (e.g. the observation archive's first poll lands before the task archive's, at module
   startup) — indistinguishable from inside `get_task()` alone. Once (1) is fixed, that
   would mean a real cancel PUT on a task that's actually fine. Guarded via
   `task_archive.last_changed()`, which is `None` until the first successful poll (existing
   behavior on `PortalTaskArchive`) — skip canceling while true, keep the original log-and-skip.
3. **`get_current_observation()` must not cancel.** An in-progress observation's task going
   unresolvable mid-run (deactivated while the mastermind is executing it) shouldn't flip the
   portal record to `canceled` out from under a running task — that produces two divergent state
   views. Reverted `get_current_observation()` to its original inline log-and-skip; only
   `get_next_observation()`'s pending path self-heals. (This path was already unreachable in
   practice pre-fix-1 anyway, since the scheduler's own archive cache is always empty and the
   mastermind never calls it with a task_archive that would trigger the bug — but the intent is
   now explicit in the code, not just true by accident.)

Also added a per-observation `LogThrottle` (`self._cancel_error_throttle`, same pattern as the
existing `self._poll_error_throttle`) around the "failed to mark canceled" log line, so a
persistent portal outage during the cancel PUT doesn't re-log an ERROR every ~5 s poll.

### Out of scope

pyobs-portal cascading deactivation to observations (root cause, separate repo, not tracked by
this plan).

## Testing

`tests/modules/robotic/test_scheduler.py`:

- `test_update_schedule_removed_task_not_in_schedule_skips_update` — delete. It no longer
  describes real behavior; a removal that isn't the currently-running task now always triggers
  `_need_update = True`.
- `test_update_schedule_removed_task_in_schedule_triggers_update` — keep, drop the
  `scheduler._schedule.get_schedule` mock (no longer consulted), assert `_need_update is True`.
- Add: removing a task that is *not* the currently-running one triggers `_need_update = True`
  even when `self._schedule.get_schedule()` returns an empty `ObservationList` (the portal-archive
  case this issue is about — currently the missing regression test).
- Existing `test_update_schedule_only_current_task_removed_skips_update` stays unchanged
  (untouched code path).

`tests/robotic/storage/portal/test_portal_archives.py`:

- `get_next_observation()`: when `task_archive.get_task()` returns `None` for the pending
  observation's task ID (and `last_changed()` returns non-`None`, i.e. the task archive has
  polled), assert the method returns `None`, `update_observation()` was called with the same
  observation now carrying `state=CANCELED` **and `task` still set to the original id** (the
  payload bug's regression test — `call_args[1]["json"]["task"] == 99`), and `obs.state` is
  mutated in the archive's own `_observations` list (a second call in the same poll cycle doesn't
  re-invoke `fetch_task()`/`update_observation()` for the same observation).
- `get_next_observation()` with `task_archive.last_changed()` returning `None` (never polled):
  assert the observation stays `PENDING` and `update_observation()` is not called — the
  startup-race guard.
- `get_current_observation()` with an unresolvable task: assert it still just logs-and-skips
  (`state` stays `IN_PROGRESS`, no PUT) — locks in that this path was deliberately *not* changed
  to self-heal.
- `update_observation()` raising inside the cancel path is caught and logged, not propagated —
  `get_next_observation()` still returns `None` cleanly rather than raising out of the mastermind's
  poll loop.

Both files: `ruff` + `pyrefly` on touched files.

## Rollout

No config changes, no migration. Both changes are self-contained to `pyobs-core`; a portal
deployment picks up the fix on next `pyobs-core` upgrade + module restart. Rollback is reverting
the PR — the scheduler gate returns (bug reappears), the mastermind falls back to log-and-skip
forever on an unresolvable task (no data loss either way, since nothing here touches
already-completed observations).

## Consequences

- **Good:** a portal task deactivation/deletion reschedules within one poll cycle instead of
  wedging the mastermind until the stale observation's window naturally expires.
- **Good:** removes a latent `AttributeError` (`s.task.id` on a bare-int FK) from the gate, as a
  side effect of deleting the code that could hit it.
- **Good:** orphaned observations self-heal (canceled) instead of spamming ERROR logs every ~10 s
  for the lifetime of their window.
- **Cost:** occasional extra reschedule runs on archives with a populated `get_schedule()` cache
  (e.g. LCO) where the removed task genuinely wasn't in the computed schedule. Accepted — bounded
  cost, no correctness impact.
- **Risk:** `get_next_observation()`/`get_current_observation()` gain a write side effect (HTTP
  PUT) on an unresolved-task path. Scoped to a genuinely-broken observation only; failure of the
  PUT itself is caught and logged, not propagated.
