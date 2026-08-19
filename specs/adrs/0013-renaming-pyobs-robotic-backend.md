# Renaming pyobs-robotic-backend

status: proposed

date: 2026-08-19

Repos: pyobs-core (this doc), pyobs-robotic-backend, pyobs-auth

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
* **`pyobs-schedule`** — recommended (proposed): names the domain object the service owns —
  the *schedule*: tasks to be observed plus the observation history. It complements the
  core scheduler instead of colliding with it (scheduler computes, schedule
  stores/serves), it is a plain descriptive noun matching the fleet convention, and the
  storage layer already speaks this vocabulary (`get_schedule`, `clear_schedule` on the
  observation archive). No `Schedule` class exists in `pyobs-core` to clash with, and no
  GitHub/PyPI collision was found.

## Decision Outcome

Proposed decision, pending team confirmation: rename `pyobs-robotic-backend` to
**`pyobs-schedule`** — GitHub repo `pyobs/pyobs-robotic-backend` → `pyobs/pyobs-schedule`,
Python package `pyobs_robotic_backend` → `pyobs_schedule`, Docker image
`ghcr.io/pyobs/pyobs-robotic-backend` → `ghcr.io/pyobs/pyobs-schedule`, Keycloak client
id `robotic-backend` → `schedule`. This is a recommendation, not a settled decision: if
the team picks a different name from Considered Options, only this section changes; the
rejected alternatives above document why the others were ruled out.

This ADR covers the *name only*: the REST API surface (`/api/...` endpoints, auth
mechanisms) is unchanged by the rename. "Robotic backend" can stay as a human
description where it helps ("the schedule service — pyobs's robotic-observatory
backend").

### Rename surface (execution checklist, in lockstep)

*In `pyobs-robotic-backend`:* repo name; `pyproject.toml` project name; package dir
`pyobs_robotic_backend/` → `pyobs_schedule/` (Django project label in `settings.py`,
`manage.py`, `wsgi.py`/`asgi.py`, Celery app name in `celery.py`, `INSTALLED_APPS`,
`urls.py`); `README.md` (title, image refs, env table incl. the `robotic-backend`
Keycloak client id default); `Dockerfile`, `docker-compose.yml`, `.env.example`,
`nginx.conf.example`, `entrypoint.sh` (image and service references).

*In `pyobs-core`:* docstrings in
`pyobs/robotic/storage/backend/taskarchive.py` (2×) and `observationarchive.py` (1×);
specs `specs/design/obsnum_fits_header.md`, `specs/design/shared-auth-keycloak.md`,
`specs/adrs/0011-keycloak-identity-broker-for-shared-auth.md` and its `index.md` entry
(Repos lines and inline mentions).

*In `pyobs-auth`:* `README.md` (2× mentions), `pyobs_auth/authentication.py` (comment).

*Deployments:* docker-compose service names/volumes and env files, Keycloak realm
configuration (client id + redirect URIs), any external docs or scripts referencing the
old repo/image name.

### Consequences

* Good, because the name says what the service is (the schedule), matches the fleet's
  descriptive-noun convention, is shorter, and doesn't collide with the scheduler in
  `pyobs-core`.
* Good, because it shares vocabulary with the storage layer (`get_schedule`,
  `clear_schedule`) and with how the scheduler consumes the service — "the backend that
  serves the schedule".
* Neutral, because a GitHub repo rename preserves history and redirects old URLs, but
  the package rename is real churn: imports, configs, and docs move together.
* Bad, because the rename surface above is spread across three repos plus deployments —
  every reference must move in lockstep, deployments must pull the new image, and the
  Keycloak client must be re-registered; stale old-name references will linger in docs
  until touched.
