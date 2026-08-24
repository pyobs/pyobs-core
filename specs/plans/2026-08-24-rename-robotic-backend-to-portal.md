# Plan: Rename pyobs-robotic-backend → pyobs-portal

Status: proposed, not started.

Decision record: `specs/adrs/0013-renaming-pyobs-robotic-backend.md` (accepted
2026-08-24, name is `pyobs-portal`). This plan is the execution checklist; the ADR's own
"Rename surface" section is the short version, this is the full one with file-level
detail gathered by grepping the fleet on 2026-08-24.

Repos: pyobs-core, pyobs-robotic-backend, pyobs-auth, pyobs-archive, pyobs-web-admin,
pyobs-iagvt, pyobs-monet (deployment configs only).

## Ordering constraint

The `pyobs-core` class rename is a breaking import-path change for any deployment YAML
naming the old dotted path (`pyobs.robotic.storage.backend.BackendTaskArchive` /
`BackendObservationArchive`). Confirmed live in two deployments today:
`pyobs-iagvt/config/iagvtsrv/{scheduler,mastermind}.yaml` and
`pyobs-monet/config/south/monet/{scheduler,mastermind}.yaml`. Sequence:

1. Land the `pyobs-robotic-backend` → `pyobs-portal` repo/package rename (Step 1) —
   independent of pyobs-core, can go first or in parallel.
2. Land the `pyobs-core` storage rename (Step 2) as a release with a clear breaking-change
   note in `CHANGELOG.rst`.
3. Before or in the same window as upgrading `pyobs-core` on iagvt/monet, update those two
   deployments' YAML dotted paths (Step 5). Do not upgrade the pinned `pyobs-core` version
   on those hosts until the YAML is updated — there is no deprecation shim, per this
   repo's rename convention (see `specs/plans/2026-08-09-night-archive-io-hardening.md`,
   which did a clean `Night`→`Reduction` rename the same way).

## Step 1 — `pyobs-robotic-backend` repo/package rename

- [ ] GitHub repo rename `pyobs/pyobs-robotic-backend` → `pyobs/pyobs-portal` (preserves
      history, issues, and redirects old URLs — GitHub does this automatically)
- [ ] `pyproject.toml`: `name = "pyobs-robotic-backend"` → `"pyobs-portal"`
- [ ] `package.json`: `"name": "pyobs-robotic-backend"` → `"pyobs-portal"`
- [ ] Package dir `pyobs_robotic_backend/` → `pyobs_portal/`, updating every internal
      reference to the old dotted path:
  - `manage.py` — `DJANGO_SETTINGS_MODULE` default
  - `pyobs_portal/settings.py` — `INSTALLED_APPS` (`pyobs_robotic_backend.api`,
    `.authentication`, and the conditional `.frontend` append), `ROOT_URLCONF`,
    `TEMPLATES` context processors (`pyobs_logo`, `keycloak`), `WSGI_APPLICATION`,
    `USER_RESOLVER` (`pyobs_robotic_backend.authentication.keycloak.resolve_user`),
    `KEYCLOAK` block's `CLIENT_ID` default (`"robotic-backend"` → `"portal"`)
  - `pyobs_portal/wsgi.py`, `asgi.py` — settings module reference
  - `pyobs_portal/celery.py` — `DJANGO_SETTINGS_MODULE` default, `Celery("pyobs_robotic_backend")`
    app name → `Celery("pyobs_portal")`
  - `pyobs_portal/urls.py`, `api/urls.py`, `api/apps.py`, `authentication/apps.py`,
    `frontend/apps.py` — Django app `name`/`label` strings
  - `authentication/keycloak.py`, `authentication/tests.py`, `api/tests.py`,
    `api/tasks.py`, `api/management/commands/mark_window_expired.py`,
    `task_scheduler.py` — internal imports
- [ ] `README.md` — title, image references, env var table (`KEYCLOAK_CLIENT_ID` default
      `robotic-backend` → `portal`)
- [ ] `docker-compose.yml` — `image: ghcr.io/pyobs/pyobs/pyobs-robotic-backend:latest`
      (3 occurrences: web, celery worker, task-scheduler script) → `pyobs-portal`
- [ ] `.env.example` — `KEYCLOAK_CLIENT_ID=robotic-backend` → `portal`
- [ ] `uv.lock` — regenerate after `pyproject.toml` rename
- [ ] `specs/index.md` and any plan docs in this repo referencing the old name in prose
      (`specs/plans/2026-08-24-module-ref-dropdowns.md`,
      `2026-08-20-connect-pyobs-archive.md`, `2026-08-20-script-builder.md`) — leave
      *closed* plans' historical prose as-is unless it names a code identifier that moved;
      update only actual dotted-path/import references

## Step 2 — `pyobs-core` storage rename (this repo)

- [ ] `pyobs/robotic/storage/backend/` → `pyobs/robotic/storage/portal/` (git mv, not
      delete+recreate, to preserve blame)
  - `taskarchive.py`: class `BackendTaskArchive` → `PortalTaskArchive`; docstring "Task
    archive based on pyobs-robotic-backend." → "...pyobs-portal."; every "backend" in
    comments/log messages referring to this service ("the backend's update marker",
    "Failed to update tasks from backend", "the backend's `last_task_update` marker",
    "an unordered backend queryset") → "portal"; `__all__`
  - `observationarchive.py`: class `BackendObservationArchive` →
    `PortalObservationArchive`; same docstring/comment/log-message sweep ("Opens the
    backend observation archive", "Closes the backend observation archive", "the
    backend's `last_observation_update` marker", "Failed to update observations from
    backend", "the backend serializes `task` as a plain FK ID"); `__all__`
  - `__init__.py`: import and `__all__` update
  - Update `pyobs-robotic-backend#84`/`#82`/`#79` issue references in comments to
    `pyobs-portal#84` etc. (GitHub redirects old-repo issue URLs after rename, but the
    dotted reference in source should track the current name)
- [ ] `tests/robotic/storage/backend/` → `tests/robotic/storage/portal/`;
      `test_backend_archives.py` → `test_portal_archives.py`; update class references and
      any `make_obs_archive()`-style fixture naming inside
- [ ] `docs/source/api/robotic/scheduling.rst`: "**Backend**
      (`pyobs.robotic.storage.backend`)" heading → "**Portal**
      (`pyobs.robotic.storage.portal`)"; prose "managed by the *pyobs-robotic-backend* HTTP
      service" → "*pyobs-portal*"; `autoclass` directives for both classes
- [ ] `docs/source/api/robotic/index.rst`: table row `pyobs.robotic.storage.backend` →
      `pyobs.robotic.storage.portal`, prose update; ASCII diagram comment "← task pool
      (files, backend, LCO portal)" → "(files, portal, LCO portal)" — flag the resulting
      "portal, LCO portal" phrasing for a human editing pass, it reads awkwardly and needs
      a human decision on wording, not a mechanical find/replace
- [ ] `docs/source/recipes/robotic.rst`: `:class:` refs to both renamed classes; "the
      *pyobs-robotic-backend* service" prose
- [ ] `specs/design/obsnum_fits_header.md`: "Repos:" line; inline `pyobs-robotic-backend`
      mentions (repo name, `pyobs_robotic_backend/api/models.py` path references — this
      doc is *implemented, closed*, so only update the repo/package name references, not
      the historical narrative)
- [ ] `specs/design/shared-auth-keycloak.md`: "Repos:" line; every inline
      `robotic-backend`/`pyobs-robotic-backend` mention (this doc is still open/reference
      material per its own status, check before editing prose vs. just names); update
      `pyobs/robotic/storage/backend/taskarchive.py` path reference to
      `pyobs/robotic/storage/portal/taskarchive.py`
- [ ] `specs/adrs/0011-keycloak-identity-broker-for-shared-auth.md`: "Repos:" line
- [ ] `specs/adrs/index.md`: 0011 entry's "Repos:" line; 0013 entry — already updated in
      this pass (see below)
- [ ] `specs/design/index.md`: entries referencing `pyobs-robotic-backend` in "Repos:"
      lines
- [ ] `specs/steering/fleet-open-items.md`: "Open decisions" ADR 0013 bullet — update once
      this plan lands (see Step 6)
- [ ] `CHANGELOG.rst`: add an entry under the unreleased section
      (`v2.0.0.dev78 (unreleased)` or whatever the head is at merge time) noting the
      breaking rename: `pyobs.robotic.storage.backend` → `pyobs.robotic.storage.portal`,
      `BackendTaskArchive`/`BackendObservationArchive` →
      `PortalTaskArchive`/`PortalObservationArchive`, with a pointer to ADR 0013. Do not
      edit past changelog entries (lines mentioning `BackendTaskArchive` etc. under
      already-released versions) — those describe behavior as it shipped under the old
      name.
- [ ] Run `pyrefly` and `pytest` after the rename — the class rename touches an abstract
      base's concrete implementation, `pyrefly` should catch any stray reference

## Step 3 — `pyobs-auth`

- [ ] `README.md` — 2 mentions of `pyobs-robotic-backend` (prose, both about the set of
      services `pyobs-auth` is shared across)
- [ ] `pyobs_auth/authentication.py` — comment "archive/robotic-backend/etc."

## Step 4 — `pyobs-archive`

- [ ] `README.md` — `ROBOTIC_BACKEND_URL` env var table row and prose mention; **decide
      here whether the env var itself is renamed** (e.g. `PORTAL_URL`) — this is a
      deployment-facing name independent of the ADR's Python-identifier scope, archive's
      own call; if renamed, keep a fallback read of the old name for one release to avoid
      breaking existing deployments silently
- [ ] `.env.example` — same var, matching README decision
- [ ] `pyobs_archive/settings.py` — comment above the env var
- [ ] `pyobs_archive/api/management/commands/sync_projects.py` — docstring mention
- [ ] `pyobs_archive/api/models.py` — docstring "Local mirror of a pyobs-robotic-backend
      Project..."
- [ ] `pyobs_archive/api/backend.py` — module docstring "Client for the
      pyobs-robotic-backend API." and class docstring; consider whether the file itself
      (`backend.py`) should move to `portal.py` for consistency — archive's call, not
      forced by this plan, since the class inside is a generic REST client wrapper, not a
      `pyobs.robotic.storage` subclass

## Step 5 — Deployment YAML (fleet)

- [ ] `pyobs-iagvt/config/iagvtsrv/scheduler.yaml`:
      `pyobs.robotic.storage.backend.BackendTaskArchive` → `.storage.portal.PortalTaskArchive`,
      `BackendObservationArchive` → `PortalObservationArchive`
- [ ] `pyobs-iagvt/config/iagvtsrv/mastermind.yaml`: same two dotted-path updates
- [ ] `pyobs-monet/config/south/monet/scheduler.yaml`: same two dotted-path updates
- [ ] `pyobs-monet/config/south/monet/mastermind.yaml`: same two dotted-path updates
- [ ] Confirm no other live site config (iag50, brot, gemini, monti) uses the backend
      archive classes — grepped 2026-08-24, none found; re-check at execution time in case
      a config was added since
- [ ] `pyobs-iagvt_1.x/config/{robotic,scheduler}.yaml` and
      `pytel-dev/configs/{scheduler2,mastermind2}.yaml` also reference the old dotted
      path — **out of scope**, these are the frozen 1.x branch and legacy pre-pyobs
      configs respectively, not live deployments

## Step 6 — `pyobs-web-admin`

- [ ] Prose-only comment updates in `modules/views.py` (2 mentions), `modules/services.py`,
      `modules/tests.py`, `pyobs_web_admin/authentication/keycloak.py`,
      `pyobs_web_admin/authentication/admin_sync.py` — no code identifiers involved, just
      `robotic-backend` → `portal` in comment text

## Step 7 — close the loop

- [ ] Update `specs/steering/fleet-open-items.md`'s "Open decisions" ADR 0013 bullet to
      reflect the rename landed (or drop it once all steps above are done)
- [ ] Update `specs/plans/index.md` — move this plan's entry to the closed section once
      Steps 1-6 are merged, noting which PRs/repos landed
- [ ] Rename this ADR's own filename is *not* needed — ADRs keep their number/filename
      after acceptance (precedent: `0011-keycloak-identity-broker-for-shared-auth.md`
      stayed put after being superseded)

## Open questions (need a decision before or during execution, not blocking the plan write-up)

1. `pyobs-archive`'s `ROBOTIC_BACKEND_URL` env var — rename to match, or leave as a stable
   deployment-facing name that just happens to point at a differently-named service? Both
   are defensible; pick one before Step 4 and note the choice here.
2. `pyobs-archive/pyobs_archive/api/backend.py` — rename the file to `portal.py`, or leave
   it since it's a thin generic REST client wrapper rather than a `pyobs.robotic.storage`
   subclass? Archive maintainer's call.
3. Whether the GitHub org's Docker image path is genuinely
   `ghcr.io/pyobs/pyobs/pyobs-robotic-backend` (double `pyobs/pyobs`, as found in
   `docker-compose.yml`) or a typo predating this plan — worth fixing to
   `ghcr.io/pyobs/pyobs-portal` while touching this line anyway, confirm against the
   actual GHCR package before Step 1.
