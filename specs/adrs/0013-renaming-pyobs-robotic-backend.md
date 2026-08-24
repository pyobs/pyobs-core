# Renaming pyobs-robotic-backend

status: accepted

date: 2026-08-19, decided 2026-08-24

Repos: pyobs-core (this doc), pyobs-robotic-backend, pyobs-auth, pyobs-archive, pyobs-web-admin

## Context and Problem Statement

`pyobs-robotic-backend` is the Django/DRF service that stores and serves the observation
task queue (tasks = observations to be scheduled), projects, and observation history,
consumed by the pyobs scheduler and related tools; it also ships a Bootstrap web frontend
and schema introspection. In `pyobs-core` terms it is the HTTP implementation of the
storage backends the scheduler uses: `BackendTaskArchive`/`BackendObservationArchive`
(`pyobs/robotic/storage/backend/taskarchive.py`, `observationarchive.py`) point their REST
calls at it.

Every other `pyobs-*` repo is named with a plain descriptive noun:

- **Services/UI**: `archive`, `auth`, `pipeline`, `task-editor`, `web-admin`,
  `web-client`, `tui`, `gui`
- **Drivers**: named after the hardware or observatory they talk to (`asi`, `sbig`,
  `qhyccd`, `zaber`, `gemini`, `monet`, `brot`, `monti`)

The only codename-style exception is `pyobs-polaris` (the clean-room C++/QML client).

`robotic-backend` is the odd one out in this fleet: it describes an *architectural role*
("a backend") rather than what the service *is*, it is the longest fleet name, and it
doesn't distinguish it from other backends (`pyobs-archive` is equally "a backend
service"). The naming question is: what descriptive noun fits this service?

## Considered Options

* **Keep `pyobs-robotic-backend`** — rejected: generic/architectural, not descriptive of
  the service's role, longest name in the fleet, breaks the plain-noun convention.
* **`pyobs-scheduler`** — rejected: clashes with the scheduler in `pyobs-core`
  (`pyobs/modules/robotic/scheduler.py` `Scheduler`; `pyobs/robotic/scheduler/`
  `TaskScheduler`, `AstroplanScheduler`, `OnDemandScheduler`). The scheduler *computes*
  schedules; this service does not, and the name would mislead about which component does
  what.
* **`pyobs-taskqueue`** — rejected: hard to pronounce as a compound, and it only names
  the task queue — not the projects or the observation history the service also stores.
* **`pyobs-ledger` / `pyobs-almanac`** — rejected: too abstract — metaphors rather than
  plain descriptions, which breaks the descriptive-noun convention the rest of the fleet
  follows.
* **`pyobs-queue`** — considered: the most concrete candidate ("it *is* the task
  queue"). Rejected for the same pronunciation concern as `taskqueue` and for covering
  only part of the stored data.
* **`pyobs-operations`** — considered: honest ("the observatory-operations backend") and
  easy to say, but broader than the service actually is and conceptually overlaps
  `pyobs-web-admin`.
* **`pyobs-planning`** — considered: easy to pronounce, but the service *stores* plans
  rather than doing the planning — a mismatch.
* **`pyobs-portal`** — **chosen** (see Decision Outcome). Names the
  service by its human-facing function: the Bootstrap frontend it ships (dashboard, task
  create/edit with schema-driven forms, user/project admin panels) makes it a genuine
  observation-management portal — functionally the counterpart of LCO's
  `observation-portal`, which this deployment also runs (brokered through Keycloak). The
  `pyobs-` prefix disambiguates rather than collides: it *pairs* with `observation-portal`
  and states the architecture mapping in the name. Easy to pronounce, a plain literal
  noun, passes the fleet convention. Loses only on naming axis: it names the function, not
  the domain object the service owns; it foregrounds the UI while the service's primary
  consumers are machines (the scheduler via `BackendTaskArchive`/`BackendObservationArchive`,
  and pyobs-task-editor); and "the portal" stays ambiguous in conversation in a deployment
  running both. If the team prefers the function-axis name, this is the pick; the
  recommendation below stays `pyobs-schedule`.
* **`pyobs-schedule`** — was the analysis's recommendation, not chosen (see Decision Outcome):
  names the domain object the service owns —
  the *schedule*: tasks to be observed plus the observation history. It complements the
  core scheduler instead of colliding with it (scheduler computes, schedule
  stores/serves), it is a plain descriptive noun matching the fleet convention, and the
  storage layer already speaks this vocabulary (`get_schedule`, `clear_schedule` on the
  observation archive). No `Schedule` class exists in `pyobs-core` to clash with, and no
  GitHub/PyPI collision was found.

## Decision Outcome

Decided 2026-08-24: rename `pyobs-robotic-backend` to **`pyobs-portal`**, not the
`pyobs-schedule` the analysis above recommended. Team picked the function-axis name
(Considered Options, `pyobs-portal` bullet: it names the Bootstrap frontend's role as an
observation-management portal and pairs with LCO's `observation-portal`, which this
deployment also runs). The naming-axis trade-off recorded in that bullet stands as the
known cost of this choice: "the portal" stays ambiguous in conversation in a deployment
that runs both a pyobs portal and an LCO `observation-portal`, and the name foregrounds
the UI even though the scheduler and pyobs-task-editor are its primary machine
consumers. That trade-off is accepted, not reopened.

Full rename mapping: GitHub repo `pyobs/pyobs-robotic-backend` → `pyobs/pyobs-portal`,
Python package `pyobs_robotic_backend` → `pyobs_portal`, Docker image
`ghcr.io/pyobs/pyobs-robotic-backend` → `ghcr.io/pyobs/pyobs-portal`, Keycloak client id
`robotic-backend` → `portal`.

This ADR covers the *name only*: the REST API surface (`/api/...` endpoints, auth
mechanisms) is unchanged by the rename. "Robotic backend" can stay as a human
description where it helps ("the portal service — pyobs's robotic-observatory
backend").

In `pyobs-core` specifically, the rename extends past the service reference: the storage
backend that talks to this service — `pyobs.robotic.storage.backend`
(`BackendTaskArchive`, `BackendObservationArchive`) — is renamed to
`pyobs.robotic.storage.portal` (`PortalTaskArchive`, `PortalObservationArchive`), so the
module/class names track the service they front rather than the generic architectural
role. Execution detail (file-by-file checklist, deploy-time YAML dotted-path updates
across the fleet) lives in
`specs/plans/2026-08-24-rename-robotic-backend-to-portal.md`, not here.

### Rename surface (execution checklist, in lockstep)

*In `pyobs-robotic-backend`:* repo name; `pyproject.toml` project name (`package.json`
`name` too — frontend test tooling); package dir `pyobs_robotic_backend/` →
`pyobs_portal/` (Django project label in `settings.py`, `manage.py`, `wsgi.py`/`asgi.py`,
Celery app name in `celery.py`, `INSTALLED_APPS`, `ROOT_URLCONF`, `WSGI_APPLICATION`,
`urls.py`, `KEYCLOAK_CLIENT_ID` default); `README.md` (title, image refs, env table incl.
the `robotic-backend` Keycloak client id default and `ROBOTIC_BACKEND_URL`-style vars in
*other* repos' env tables — see pyobs-archive below); `docker-compose.yml`,
`.env.example`, `nginx.conf.example`, `entrypoint.sh` (image and service references).

*In `pyobs-core`:* `pyobs/robotic/storage/backend/` → `pyobs/robotic/storage/portal/`
(both files, `__init__.py` exports); class renames `BackendTaskArchive` →
`PortalTaskArchive`, `BackendObservationArchive` → `PortalObservationArchive`; docstrings
and inline comments referring to "the backend" as this service (both files); test dir
`tests/robotic/storage/backend/` → `tests/robotic/storage/portal/`; docs
(`docs/source/api/robotic/scheduling.rst`, `docs/source/api/robotic/index.rst`,
`docs/source/recipes/robotic.rst`); specs `specs/design/obsnum_fits_header.md`,
`specs/design/shared-auth-keycloak.md`,
`specs/adrs/0011-keycloak-identity-broker-for-shared-auth.md` and its `index.md` entry
(Repos lines and inline mentions); `specs/design/index.md`;
`specs/steering/fleet-open-items.md`. New `CHANGELOG.rst` entry under the unreleased
section noting the breaking import-path change; do not rewrite past changelog entries
that describe old-named behavior at the time it shipped.

*In `pyobs-auth`:* `README.md` (2× mentions), `pyobs_auth/authentication.py` (comment).

*In `pyobs-archive`:* prose mentions in `README.md`, `.env.example`,
`pyobs_archive/settings.py`, `pyobs_archive/api/management/commands/sync_projects.py`,
`pyobs_archive/api/models.py`, `pyobs_archive/api/backend.py` (docstrings/comments); the
`ROBOTIC_BACKEND_URL` env var is a public deployment-facing name — archive's own call,
document in the plan whether it's renamed (with a deprecation read-fallback) or left
alone, since renaming it is a deployment-config break independent of this ADR's service
rename.

*In `pyobs-web-admin`:* prose-only comments in `modules/views.py`, `modules/services.py`,
`modules/tests.py`, `pyobs_web_admin/authentication/keycloak.py`,
`pyobs_web_admin/authentication/admin_sync.py` — no identifiers to rename, just wording.

*Deployments (fleet-wide):* every `class: pyobs.robotic.storage.backend.Backend*Archive`
dotted path in scheduler/mastermind YAML configs must move to
`pyobs.robotic.storage.portal.Portal*Archive` in lockstep with the pyobs-core release —
confirmed present in `pyobs-iagvt` (`config/iagvtsrv/{scheduler,mastermind}.yaml`) and
`pyobs-monet` (`config/south/monet/{scheduler,mastermind}.yaml`); docker-compose service
names/volumes and env files, Keycloak realm configuration (client id + redirect URIs),
any external docs or scripts referencing the old repo/image name.

*Explicitly out of scope:* `pyobs-core_1.x` (frozen 1.x snapshot) and `pytel-dev`
(legacy pre-pyobs configs) also contain `storage.backend`/`Backend*Archive` references;
these are frozen/legacy and not part of the active fleet, so leave them untouched unless
someone is actively working in them.

### Consequences

* Good, because the name says what the service is (the schedule), matches the fleet's
  descriptive-noun convention, is shorter, and doesn't collide with the scheduler in
  `pyobs-core`.
* Good, because it shares vocabulary with the storage layer (`get_schedule`,
  `clear_schedule`) and with how the scheduler consumes the service — "the backend that
  serves the schedule".
* Neutral, because a GitHub repo rename preserves history and redirects old URLs, but
  the package rename is real churn: imports, configs, and docs move together.
* Bad, because the rename surface above is spread across five repos
  (`pyobs-robotic-backend`, `pyobs-core`, `pyobs-auth`, `pyobs-archive`,
  `pyobs-web-admin`) plus deployments — every reference must move in lockstep,
  deployments must pull the new image, and the Keycloak client must be re-registered;
  stale old-name references will linger in docs until touched.
* Bad, because in `pyobs-core` the class rename (`BackendTaskArchive` →
  `PortalTaskArchive`, `BackendObservationArchive` → `PortalObservationArchive`) is a
  breaking import-path change for every deployment YAML that names the old dotted path —
  confirmed live in `pyobs-iagvt` and `pyobs-monet` — so it must ship in lockstep with
  those configs' updates, not land ahead of them.
