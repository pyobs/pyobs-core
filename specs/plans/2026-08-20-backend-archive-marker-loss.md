# Plan: Stop gating backend-archive refreshes on the `last_*_update` marker

Status: implemented, closed (merged 2026-08-20, PR #795)
Repos: pyobs-core, pyobs-robotic-backend
Issue: pyobs-core#789

## Problem

The Mastermind keeps running stale tasks: edits to tasks (duration, script, priority,
`active`) and newly scheduled observations made in the pyobs-robotic-backend never reach the
running mastermind, and window-expired observations stay runnable. Verified in the field and
pinned down in issue #789:

1. `BackendTaskArchive._check_for_changes()` (`pyobs/robotic/storage/backend/taskarchive.py`)
   and `BackendObservationArchive._check_for_changes()`
   (`pyobs/robotic/storage/backend/observationarchive.py`) poll
   `GET /api/last_task_update/` resp. `/api/last_observation_update/` every 5 s and only
   re-download tasks/observations when the returned timestamp is newer than the locally cached
   `_last_update`.
2. The backend computes those timestamps purely from a Django cache marker (`post_save`
   receivers running `cache.set("last_task_update", ...)`, views returning
   `cache.get("last_task_update", Time("1970-01-01T00:00:00"))`).
3. `CACHES` uses `LocMemCache` — an in-memory cache that is **per process**, and the deployment
   runs 4 gunicorn workers plus separate `celery`/`task_scheduler` processes. A marker set in
   the worker that handled a write is invisible to every other worker, so most polls return the
   `1970-01-01` fallback. The archive then initializes `_last_update` from that fallback, and
   `_last_update < last_update` is never true again → the archives never re-download.
4. `mark_window_expired`/`delete_old_observations` (`api/tasks.py`) use `QuerySet.update()` /
   `.delete()`, which never fire `post_save` — those state changes never bump the marker even in
   a single-worker setup.

Because the Mastermind resolves observation `task` IDs from the archive's cached task list on
every poll (`Observation.fetch_task()`), the staleness is entirely in the archives not
re-downloading, not in stale embedded data. Fixing the pyobs-core side makes the mastermind
robust regardless of the backend's marker behavior.

## Design

Drop the marker as the refresh gate. The archives re-fetch **unconditionally on every poll**
(payloads are small: a few dozen tasks/projects/observations) and detect real changes by
comparing the downloaded content against the cached copy. This matches the issue's suggested
fix ("re-fetch unconditionally on each poll ... or compare list contents/hash to detect
changes; treat a missing/older marker as 'refresh anyway'").

### `BackendTaskArchive`

- Extract the loop body into a testable `_update()` method; `_check_for_changes()` keeps the
  `while True` / try-except / `asyncio.sleep(5)` shell.
- `_update()` fetches projects + tasks, compares against the cached lists via
  `model_dump()` output, and only on a real difference replaces the cache, sets
  `_last_update = Time.now()`, and fires `_on_tasks_changed`.
- Comparison must be on `model_dump()`, **not** on pydantic `==`: `Task.__eq__` compares
  `__dict__`, which also contains runtime attributes set during execution (e.g.
  `Task._cant_run_reason` from `can_run()`), so a task that has merely *run* would look
  different from a freshly downloaded one on every poll. `model_dump()` serializes only declared
  fields, so it is stable. (Verified against the installed pydantic.)
- `_last_update` is never initialized from the backend marker anymore, so the `1970-01-01`
  fallback can't pin the archive. `last_update_time()` stays as a public method (the endpoint
  still exists; the robotic-backend side may fix the marker later) but is no longer used for
  gating.
- `last_changed()` now returns the local time at which a content change was last observed —
  semantically "last time tasks changed" from this archive's point of view.

### `BackendObservationArchive`

Same shape:

- `_update()` fetches the schedule (`get_observations(end_after=now, state=pending|in_progress)`)
  and compares full observation contents via `model_dump(use_task_id=True)`.
- `use_task_id=True` matters twice: the backend serializes `task` as a plain FK ID, while the
  cached copies get their `task` replaced by a full `Task` when the mastermind calls
  `fetch_task()` — the flag normalizes both sides to the task ID.
- Comparison must cover **all fields including `state`**: `Observation.__eq__` compares only
  `task.id`/`start`/`end` (ignoring `state`), so a naive list-equality check would miss
  `window_expired` / `in_progress` transitions — the exact symptom of the bug. Comparing
  `model_dump()` output catches them.
- Spurious "changed" detections (e.g. an `obsnum` the backend doesn't persist) are harmless:
  they cause a re-download and a log line, never a missed change. The dangerous direction —
  missing a real change — is what this fix eliminates.

### Out of scope (pyobs-robotic-backend)

The root-cause fixes on the backend side (shared Redis cache, or an `updated_at` column to
compute the markers from the DB; bumping markers in the celery bulk paths) live in the sibling
repo and are not part of this PR. With this change the mastermind no longer depends on any of
them for correctness.

## Testing

`tests/robotic/storage/backend/test_backend_archives.py`:

- `_update()` re-downloads and applies changes **even when the backend marker is stale/unchanged**
  (the regression: previously a pinned `_last_update` skipped the download). Mock
  `last_update_time()` to return a fixed old timestamp; assert `_get_projects`/`_get_tasks`
  were called and the cache + `_on_tasks_changed` fired.
- `_update()` does **not** fire `_on_tasks_changed` when content is unchanged (idempotent poll).
- `_update()` fires `_on_tasks_changed` when a task's content changed (e.g. `active` flipped)
  even though its identity is the same.
- Observation archive: `_update()` detects a pure **state** change (pending → window_expired)
  despite `Observation.__eq__` ignoring state.
- Observation archive: `_update()` does not spam "changed" when the cached observations had
  `fetch_task()` applied (task normalized to ID) — pins the `use_task_id` comparison.
- Existing `last_update_time()` tests stay (method is kept).
- `ruff` + `pyrefly` on touched files.

## Rollout

No config changes. The archives self-heal on restart; no migration. Rollback is reverting this
PR (the marker-gated behavior returns). The pyobs-robotic-backend marker fixes can land
independently whenever; they will only make `last_update_time()` truthful again, not change
refresh behavior.

## Consequences

- **Good:** the mastermind picks up task edits, newly scheduled observations, and
  window-expiry within one poll cycle (≤5 s) regardless of which gunicorn worker saw the write.
- **Good:** removes the per-process marker as a single point of failure for refresh; the
  fallback timestamp can no longer pin the archives.
- **Cost:** one extra GET per poll per archive (the marker request is dropped, so net traffic is
  the same or less); re-downloading unchanged payloads every 5 s — accepted, payloads are small.
- **Risk:** content comparison depends on stable field serialization; fields the backend
  truncates/round-trips differently could cause spurious (never missed) updates. None known.
