# The pyobs project fleet: core, connected, and internal projects

pyobs-core doesn't live alone — a fleet of sibling repos (mostly hardware drivers, plus a few
GUIs/backends) depend on it and need to stay compatible with it. When doing anything fleet-wide
(surveying for a bug pattern across repos, checking who's affected by a pyobs-core API change,
deciding what needs a compatibility pass before a pyobs-core release), use this list rather than
guessing from whatever happens to be checked out locally.

## Core projects

Actively maintained, expected to track pyobs-core closely, first candidates for any fleet-wide
check or migration:

2.x/not-2.x checked 2026-08-11 against local checkouts' `pyproject.toml` `version =` line (exact
dev numbers deliberately omitted here — they churn too fast to keep current; re-check locally if
you need the precise number).

### Framework

- pyobs-core — module system, interfaces, XMPP comms, robotic scheduler (Python, uv) — 2.x

### Cameras

- pyobs-aravis — Aravis/GenICam camera driver (Python, uv) — 2.x
- pyobs-asi — ZWO ASI camera driver (Python, uv) — 2.x
- pyobs-fli — FLI camera driver (Python, uv, Cython) — 2.x
- pyobs-flipro — FLI Pro-series camera driver (Python, uv, Cython) — 2.x
- pyobs-qhyccd — QHYCCD camera driver (Python, uv, Cython) — 2.x
- pyobs-sbig — SBIG camera driver (Python, uv, Cython) — 2.x
- pyobs-tis — The Imaging Source camera driver (Python, uv) — 2.x
- pyobs-v4l — Video4Linux camera driver (Python, uv) — 2.x

### Mounts, domes, and focusers

- pyobs-alpaca — ASCOM Alpaca wrapper, a generic device wrapper over HTTP (Python, uv) — 2.x
- pyobs-brot — telescopes, domes, and roll-off roofs via BROTlib/MQTT (Python, uv) — 2.x
- pyobs-gemini — Optec Gemini rotator/focuser (Python, uv) — 2.x
- pyobs-zaber — Zaber motion-control stages (Python, uv) — 2.x
- pyobs-zwoeaf — ZWO electronic autofocuser (Python, uv) — 2.x

### User interfaces

- pyobs-gui — desktop GUI (Python, uv, PySide6/Qt6) — 2.x
- pyobs-polaris — clean-room desktop client modeled on pyobs-gui (C++20, CMake, Qt6) — not a
  Python project, no version to compare
- pyobs-web-client — browser client (TypeScript, npm, Vue 3) — not a Python project, no version
  to compare

## Connected projects

Depend on pyobs-core/the core projects but sit a layer further out (web/UI clients, task
scheduling/authoring, not drivers). See "Version policy" below for which of these are expected to
track pyobs-core's major version and which aren't:

### Task scheduling and operations

- pyobs-robotic-backend — REST API + web frontend for tasks/projects/observations/scheduling
  (Python, uv, Django + DRF) — 2.x, complies with the version policy
- pyobs-web-admin — start/stop/restart modules, tail logs, edit configs, from a browser
  (Python, uv, Django) — no pyobs-core dependency (policy doesn't apply), n/a

### Data processing and archiving

- pyobs-archive — LCO-style image archive (Python, uv, Django) — no pyobs-core dependency, n/a
- pyobs-astrometry — astrometry.net web service for plate solving; wraps the C astrometry.net
  toolchain (Python, Flask, no uv/lockfile — plain script + Dockerfile) — no local checkout to
  check
- pyobs-pipeline — reduction-pipeline monitoring/configuration (Python, uv, Django) — 2.x,
  dependency floor also 2.x. Not in scope of the version policy despite having a real dependency
  (see "Policy scope gaps" below)

### Site and environment monitoring

- pyobs-allsky-cloudcover — cloud-cover detection from allsky images, writes to InfluxDB
  (Python + Rust, Poetry/Cargo — not uv) — pyobs-core dependency is commented out in
  `pyproject.toml`, not actually installed
- pyobs-weather — weather-station aggregator with "is it good?" rules (Python, uv, Django) — no
  pyobs-core dependency, n/a

### Dashboards

- pyobs-dashboard-utils — modules for building a dashboard (Python, uv) — pyobs-core dependency
  floor is stale (`>=1.17.2`), well behind current pyobs-core; not in scope of the version policy
  despite having a real dependency (see "Policy scope gaps" below)

## Homepage

- pyobs.github.io — static site (Ruby, Jekyll, GitHub Pages)

## IAG internal projects

Specific to IAG's own telescopes/instruments, not general-purpose drivers. Not in the `pyobs`
GitHub org, so descriptions/stacks below aren't independently verified the way the rest of this
doc is:

- pyobs-iag50
- pyobs-iagvt
- pyobs-monet
- pyobs-monti

## Archived projects

Formerly listed here, no longer maintained/tracked:

- pyobs-andor — Andor camera driver. Local checkout was a dead, non-git, 2020-era `setup.py`
  folder (`version='0.2'`), never migrated to the 2.0 line. Archived 2026-08-11.
- pyobs-tui — terminal UI (Python, uv, Textual). Still on `1.0.0`, `pyobs-core>=1.34.0`, never
  migrated to the 2.0 line — unlike pyobs-andor it was still receiving pushes up to the day it
  was archived (2026-08-11).
- pyobs-task-editor — desktop app for authoring tasks (Python, uv, PySide6/Qt6). Still `0.0.1`,
  `pyobs-core>=1.54.4`, never migrated to the 2.0 line — also still receiving pushes up to the
  day it was archived (2026-08-11).

## Version policy: connected-tier projects track pyobs-core's major version

This policy applies only to connected-tier projects with a *real* `pyobs-core` dependency, and
currently only **pyobs-robotic-backend** is actually held to it (task-editor was the other
covered project until it was archived, see above).

`web-admin`/`web-client`/`polaris` have no real `pyobs-core` coupling (web-admin talks XMPP
directly, web-client is npm-only, polaris is its own C++ protocol client) — versioning them to
match pyobs-core's major would be arbitrary, don't do it just for fleet-wide uniformity.

### The policy (for pyobs-robotic-backend)

1. The project's **major version must match the major version of the pyobs-core it depends on**.
   Minor and patch versions are independent — each project keeps its own release cadence there,
   unrelated to pyobs-core's minor/patch.
2. While pyobs-core itself is on a pre-release/dev version (like now: `2.0.0.devN`), these projects
   follow the same `.devN` suffix scheme for their own releases (e.g. `2.6.devN`, not a plain
   `2.6.0`) — this signals "not yet stable against the pyobs-core version it targets," the same way
   pyobs-core's own `.devN` suffix does. Once pyobs-core cuts a stable (non-`.dev`) release for that
   major version, these projects drop the `.dev` suffix too and settle into normal semver.

This mirrors what's already established practice for the **core**-tier driver repos (pyobs-asi,
pyobs-aravis, etc.) — they've tracked pyobs-core's `2.0.0.devN` scheme all along.

pyobs-robotic-backend now complies (bumped to 2.x since the 2026-07-22 survey, when it was still
`1.6.2` on `pyobs-core>=1.54.1`).

### Policy scope gaps

pyobs-pipeline and pyobs-dashboard-utils both have real `pyobs-core` dependencies (see tier list
above) but aren't covered by "the policy" above, which is scoped narrowly to
pyobs-robotic-backend. Neither follows the major-match/`.devN` scheme on its own version either.
This is a known gap, not resolved here — flagging it rather than silently extending the policy to
projects whose maintainers haven't signed off on it. pyobs-allsky-cloudcover has a similar gap but
its `pyobs-core` dependency is currently commented out, so it's moot until that's reinstated.

Given how much changed in the 1.x -> 2.0 rewrite (breaking API changes across the fleet, seen
repeatedly in driver fixes), a project that hasn't bumped most likely doesn't actually work against
current pyobs-core yet. Bumping the version number alone would be misleading without first doing
the real compatibility work and verifying it — not something to act on unprompted; each project's
maintainer should sign off individually.

pyobs-andor, pyobs-tui, and pyobs-task-editor were all found stalled on this same 1.x -> 2.0
migration and were archived from the fleet entirely rather than fixed (see "Archived projects"
above) — none were in scope of this policy (andor/tui are core-tier, task-editor is connected-tier
but its dependency floor never moved off 1.x).

## Legacy major-version branches

When a project's major version bumps, the outgoing major version isn't just abandoned — it keeps
a branch named `<old-major>.x` (e.g. `1.x`) that can continue to receive its own patch/bugfix
releases and tags independently of `develop`/`main`, for however long that old major version still
needs support.

pyobs-core already does exactly this: its own `1.x` branch is still getting real patch releases
(`v1.54.4` as of 2026-07-14) in parallel with `2.0.0.devN` development on `develop`.
pyobs-robotic-backend already made this jump. Any future project doing the same should create the
equivalent `<old-major>.x` branch from its pre-bump state, the same way, rather than just letting
the old major version's history dead-end at the bump commit.

One thing to double-check rather than copy blindly when setting one of these up: pyobs-core's own
`1.x` branch has a `.github/dependabot.yml` still pointing `target-branch: "develop"` — i.e.
Dependabot updates for the 1.x line get raised against `develop`, not `1.x` itself. That may be a
leftover from before the branch split rather than an intentional choice; verify what's actually
wanted before replicating it on a new legacy branch.

## See also

- `specs/steering/fleet-tooling-consistency.md` — the lint/type-check/dependabot baseline every
  core+connected repo should have.
