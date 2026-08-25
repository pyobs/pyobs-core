# Plan: Rename pyobs-robotic-backend → pyobs-portal

Status: proposed, not started. Re-checked 2026-08-25 against all six repos' current
`develop`/default branches: no step below has been started anywhere (no renamed dirs,
branches, or class names found). Two updates below (Step 4, Step 5) reflect that check.

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
- [ ] `docker-compose.yml` — `image: ghcr.io/pyobs/pyobs-robotic-backend:latest` (3
      occurrences: web, celery worker, task-scheduler script) → `ghcr.io/pyobs/pyobs-portal`
      (**resolved 2026-08-25, was Open question 3**: re-checked the file, the path is a
      single `pyobs/`, not a double `pyobs/pyobs` — the earlier "double pyobs/pyobs" note
      was a misread, no typo to fix, just the straightforward image-name swap)
- [ ] `.env.example` — `KEYCLOAK_CLIENT_ID=robotic-backend` → `portal`
- [ ] `uv.lock` — regenerate after `pyproject.toml` rename
- [ ] `specs/index.md` and any plan docs in this repo referencing the old name in prose
      (`specs/plans/2026-08-24-module-ref-dropdowns.md`,
      `2026-08-20-connect-pyobs-archive.md`, `2026-08-20-script-builder.md`) — leave
      *closed* plans' historical prose as-is unless it names a code identifier that moved;
      update only actual dotted-path/import references
- [ ] **added 2026-08-25** — local checkout housekeeping on this machine (not part of the
      repo's own history, do after the GitHub rename above so `git remote -v` still
      resolves): rename the local clone directory
      `/home/husser/code/pyobs/pyobs-robotic-backend` → `/home/husser/code/pyobs/pyobs-portal`
  - `.idea/` inside it is gitignored (confirmed via `.gitignore:19`, not tracked), so it
    won't move with a repo-side rename and needs the same local touch-up: rename
    `.idea/pyobs-robotic-backend.iml` → `.idea/pyobs-portal.iml`, and update the old-name
    references inside `.idea/modules.xml` (module `fileurl`/`filepath` pointing at the
    `.iml`), `.idea/misc.xml` (`sdkName value="uv (pyobs-robotic-backend)"` →
    `"uv (pyobs-portal)"`), and `.idea/workspace.xml` (grepped 2026-08-25, also references
    the old name — PyCharm regenerates most of `workspace.xml` on next open, so a targeted
    fix is optional, just don't be surprised if it's stale until then)

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

- [ ] `README.md` — `ROBOTIC_BACKEND_URL` → `PORTAL_URL` (**resolved 2026-08-25, was Open
      question 1**: rename it) env var table row and prose mention
- [ ] `.env.example` — same var rename
- [ ] `pyobs_archive/settings.py` — `ROBOTIC_BACKEND_URL = os.environ.get('ROBOTIC_BACKEND_URL',
      '')` → `PORTAL_URL = os.environ.get('PORTAL_URL', '')`; keep a fallback read of the old
      env var name for one release (`os.environ.get('PORTAL_URL') or
      os.environ.get('ROBOTIC_BACKEND_URL', '')`) so existing deployments don't silently
      break, then drop the fallback in a follow-up release once the fleet's `.env` files are
      confirmed updated
- [ ] `pyobs_archive/api/management/commands/sync_projects.py` — docstring mention;
      `settings.ROBOTIC_BACKEND_URL`/`ROBOTIC_BACKEND_TOKEN` → `settings.PORTAL_URL`/
      `PORTAL_TOKEN`; `from pyobs_archive.api.backend import BackendClient,
      BackendUnavailable` → `from pyobs_archive.api.portal import PortalClient,
      PortalUnavailable`
- [ ] `pyobs_archive/api/models.py` — docstring "Local mirror of a pyobs-robotic-backend
      Project..."; same `settings.ROBOTIC_BACKEND_URL`/`TOKEN` and `BackendClient`/
      `BackendUnavailable` import/usage rename as above
- [ ] `pyobs_archive/api/backend.py` → `pyobs_archive/api/portal.py` (**resolved 2026-08-25,
      was Open question 2**: rename the file; git mv, not delete+recreate, to preserve
      blame) — module docstring "Client for the pyobs-robotic-backend API." → "...
      pyobs-portal API."; class `BackendClient` → `PortalClient`, exception
      `BackendUnavailable` → `PortalUnavailable` (real identifiers, not just prose —
      **correction 2026-08-25**: originally scoped as docstring-only, but
      `pyobs_archive/api/models.py` and
      `pyobs_archive/api/management/commands/sync_projects.py` both import these names, and
      `pyobs_archive/api/tests.py` references them ~15 times, including a test class named
      after it, `BackendClientPaginationTests` → `PortalClientPaginationTests`)
- [ ] `pyobs_archive/api/tests.py` — **added 2026-08-25**, missed in the original grep:
      ~15 occurrences of `self.settings(ROBOTIC_BACKEND_URL=...)` → `PORTAL_URL=...` test
      overrides; `from pyobs_archive.api.backend import BackendClient, BackendUnavailable`
      → `from pyobs_archive.api.portal import PortalClient, PortalUnavailable`; all
      `BackendClient`/`BackendUnavailable` references (mock patches, instantiations,
      assertions) and the `BackendClientPaginationTests` class name

## Step 5 — Deployment YAML (fleet)

- [ ] `pyobs-iagvt/config/iagvtsrv/scheduler.yaml`:
      `pyobs.robotic.storage.backend.BackendTaskArchive` → `.storage.portal.PortalTaskArchive`,
      `BackendObservationArchive` → `PortalObservationArchive`
- [ ] `pyobs-iagvt/config/iagvtsrv/mastermind.yaml`: same two dotted-path updates
- [ ] `pyobs-monet/config/south/monet/scheduler.yaml`: same two dotted-path updates
- [ ] `pyobs-monet/config/south/monet/mastermind.yaml`: same two dotted-path updates
- [ ] Confirm no other live site config (iag50, brot, gemini, monti) uses the backend
      archive classes — grepped 2026-08-24, none found; re-grepped 2026-08-25, still none;
      re-check at execution time in case a config was added since
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

## Open questions — resolved 2026-08-25

All three questions below are decided; Steps 1 and 4 above already reflect the outcome.

1. `pyobs-archive`'s `ROBOTIC_BACKEND_URL` env var → **renamed** to `PORTAL_URL` (with a
   one-release fallback read of the old name, see Step 4).
2. `pyobs-archive/pyobs_archive/api/backend.py` → **renamed** to `portal.py`, including its
   `BackendClient`/`BackendUnavailable` identifiers → `PortalClient`/`PortalUnavailable`
   (see Step 4).
3. The GitHub org's Docker image path — **no typo**, re-checked `docker-compose.yml`
   directly: it's a single `ghcr.io/pyobs/pyobs-robotic-backend`, not a double
   `pyobs/pyobs`. Straightforward rename to `ghcr.io/pyobs/pyobs-portal` (see Step 1).
