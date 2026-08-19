# Plan: Project-based access control for pyobs-archive

Tracks pyobs/pyobs-archive#42. Depends on pyobs/pyobs-robotic-backend#79 (per-project `public`
flag).
Repos: pyobs-archive, pyobs-robotic-backend.

Status: planned

## Problem

The archive serves every archived frame to any authenticated user: `frames_view`,
`aggregate_view`, `zip_view` and the per-frame endpoints (`frame_view`, `download_view`,
`preview_view`, `headers_view`, `catalog_view`, `related_view`) are all `IsAuthenticated` with
no per-user filtering (`pyobs_archive/api/views.py`). There is no notion of "which images may
this user see" at all — the `Frame` model has no project association
(`pyobs_archive/api/models.py`), and no source for one.

Observations are often proprietary: a user should only see images of projects they are a member
of, plus projects explicitly marked public. Project membership and the public flag are owned by
`pyobs-robotic-backend` (the `Project` model: `code` PK, `name`, `priority`, `users` M2M —
`pyobs_robotic_backend/api/models.py`; the public flag is tracked in
pyobs/pyobs-robotic-backend#79). The archive must learn projects and users from there.

## Proposal

1. **Frame → project association.** Add `Frame.PROJECT` (max 10 chars, matching
   `Project.code`), read from a `PROJECT` FITS keyword during ingestion
   (`add_fits_header()`) and exposed via `get_info()`. Dependency: FITS headers must actually
   carry `PROJECT` — the robot/pipeline writes it (pyobs-core `addfitsheaders` processor or the
   archiver), see Open questions.
2. **Project/user knowledge.** The archive learns projects and users from
   `pyobs-robotic-backend`. Recommended first step: local sync (Option B) — new `Project`
   (code, name, public) + membership models in the archive, filled by
   `manage.py sync_projects` from the backend's admin API using a service-account token. Live
   per-request query (Option A) is the later enhancement behind the same interface.
3. **Access layer.** `pyobs_archive/api/permissions.py`: `accessible_projects(user)` (superuser
   → all; otherwise public ∪ member projects) and `can_access_frame(user, frame)`. Gated by a
   `PROJECT_ACCESS_CONTROL` setting (default off → today's behavior), so deployments opt in.
4. **Filter everything.** Listing, facets, bulk download, and every single-frame endpoint (via
   the `_frame()` choke point) only return frames the user may see; unauthorized direct access
   answers 404 (not 403) so existence isn't leaked.
5. **Backend (tracked in #79).** `Project.public` flag + serializer/frontend exposure;
   non-superusers also see public projects in `GET /api/projects/`; optionally a user-scoped
   "accessible projects" query for the archive's service account.

## Implementation

### 1. Frame.PROJECT — `pyobs_archive/api/models.py`

- [ ] Add `PROJECT = models.CharField(max_length=10, null=True, default=None, db_index=True)`
      to `Frame` + migration.
- [ ] Add `'PROJECT'` to the keyword list in `add_fits_header()` (absent header → stays
      `None`).
- [ ] Expose `PROJECT` in `get_info()` so the frontend can show/filter it.

### 2. Backend connection (project/user knowledge)

Option B (recommended, first):

- [ ] Archive models mirroring the backend: `Project` (code, name, public) + user memberships
      (either a `users` M2M or per-user project rows).
- [ ] `manage.py sync_projects` management command: pull projects + memberships from the
      backend (admin-authenticated `GET /api/projects/`, `GET /api/users/` or a dedicated dump
      endpoint), upsert locally.
- [ ] Settings: `ROBOTIC_BACKEND_URL`, `ROBOTIC_BACKEND_TOKEN` (service account), optional
      sync interval / on-login trigger. Document in README/.env.example.

Option A (later enhancement, same interface):

- [ ] Resolve the current user's accessible projects live: a backend endpoint answering
      "accessible projects for user X" by Keycloak/username identity — local user IDs differ
      between the two services, but both resolve the same Keycloak `sub` via `pyobs_auth`.

### 3. Access layer — `pyobs_archive/api/permissions.py`

- [ ] `accessible_projects(user) -> set[str] | None`: `None` for superusers, else public ∪
      member project codes (from the sync table; Option A queries the backend).
- [ ] `can_access_frame(user, frame) -> bool`: superuser, or the `frame.PROJECT is None`
      policy (see Open questions), or `frame.PROJECT in accessible_projects(user)`.
- [ ] Setting `PROJECT_ACCESS_CONTROL` (bool, default `False`).

### 4. Endpoint filtering — `pyobs_archive/api/views.py`

- [ ] `frames_view`: after `filter_frames()`, restrict to accessible projects when the setting
      is on (skip for superusers).
- [ ] `aggregate_view`: same restriction so facet options don't leak counts of private images.
- [ ] `zip_view` (`zip_view_post`/`zip_view_get`): same restriction on the selected frames.
- [ ] `_frame(frame_id)`: central access check → raise `Http404` when the user lacks access
      (covers `frame_view`, `download_view`, `preview_view`, `headers_view`, `catalog_view`).
- [ ] `related_view`: filter the related-frame list itself (an accessible frame's related set
      may contain frames from other projects).

### 5. Frontend — `pyobs_archive/frontend`

- [ ] No client change strictly needed (bootstrap-table + `app.js` consume `/frames/` +
      `/frames/aggregate/`, which already return only accessible rows).
- [ ] Optional: show the user's accessible projects as a filter; empty-state handling.

### 6. Backend dependency — tracked in pyobs/pyobs-robotic-backend#79

- [ ] `Project.public` flag + migration + serializer/frontend toggle.
- [ ] `ProjectList.get_queryset`: non-superusers also see public projects.
- [ ] (Option A) user-scoped accessible-projects endpoint for the archive's service account.

## Tests

- Ingestion: `PROJECT` read from header; absent header → `None`.
- Permissions: superuser → all; member → member + public; non-member → excluded; anonymous →
  (existing 401).
- Endpoints: listing, aggregate, zip filtered; direct single-frame access → 404; related list
  filtered.
- Backend (#79): public flag in its own tests.

## Consequences

- **Good:** proprietary observations stop being visible to everyone; the access rule (public vs.
  members) matches the backend's ownership of projects and users.
- **Good:** feature-gated (`PROJECT_ACCESS_CONTROL` default off) — existing installs keep
  today's behavior until they opt in.
- **Neutral:** sync (Option B) is stale between syncs; frames without `PROJECT` need a policy
  (see Open questions).
- **Trade-off:** 404 instead of 403 hides the existence of private frames from non-members —
  including from counts/aggregates.

## Open questions

- Frames with `PROJECT = None` (legacy data / headers without the keyword): visible to all
  authenticated users, or only superusers? (compat vs. security)
- Who writes the `PROJECT` FITS keyword — pyobs-core pipeline (`addfitsheaders`), the robot,
  or the backend at observation time? (no such keyword exists anywhere today)
- Sync (B) vs. live query (A) vs. forwarding the user's Bearer token (only viable for
  Bearer-token API clients; the session-cookie web UI has no token to forward)?
- Should `related` frames of an accessible frame stay visible even if their own project is
  inaccessible?
- Do aggregate/facet counts leak existence even when the rows are filtered?
