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

- pyobs-portal — REST API + web frontend for tasks/projects/observations/scheduling (Python, uv,
  Django + DRF) — 2.x, complies with the version policy. Renamed from pyobs-robotic-backend
  (ADR `0013`, 2026-08-24)
- pyobs-web-admin — start/stop/restart modules, tail logs, edit configs, from a browser
  (Python, uv, Django) — 2.x (manually bumped 2026-08-11); no pyobs-core dependency, but the
  version policy now applies fleet-wide regardless (see "Version policy" below)

### Data processing and archiving

- pyobs-archive — LCO-style image archive (Python, uv, Django) — 2.x; no pyobs-core dependency,
  but complies with the version policy anyway
- pyobs-astrometry — astrometry.net web service for plate solving; wraps the C astrometry.net
  toolchain (Python, Flask, no uv/lockfile — plain script + Dockerfile) — no local checkout to
  check
- pyobs-pipeline — reduction-pipeline monitoring/configuration (Python, uv, Django) — 2.x,
  dependency floor also 2.x. Complies with the version policy

### Site and environment monitoring

- pyobs-allsky-cloudcover — cloud-cover detection from allsky images, writes to InfluxDB
  (Python + Rust, Poetry/Cargo — not uv) — not 2.x (`0.1.0`); pyobs-core dependency is commented
  out in `pyproject.toml`, not actually installed. Doesn't comply with the version policy
- pyobs-weather — weather-station aggregator with "is it good?" rules (Python, uv, Django) — not
  2.x (`1.3.6`); no pyobs-core dependency, but the version policy applies fleet-wide regardless —
  doesn't comply

### Dashboards

- pyobs-dashboard-utils — modules for building a dashboard (Python, uv) — not 2.x (`0.1.0`);
  pyobs-core dependency floor is also stale (`>=1.17.2`), well behind current pyobs-core. Doesn't
  comply with the version policy

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

## Version policy: every pyobs project tracks pyobs-core's major version

**Decided 2026-08-11: this now applies fleet-wide, not just to connected-tier projects with a
real `pyobs-core` dependency.** Every project in this doc — core tier, connected tier, regardless
of whether it actually imports `pyobs-core` — keeps its own major version aligned with
pyobs-core's. This supersedes the narrower "only projects with a real dependency" scoping this
section used to have.

### The policy

1. The project's **major version must match pyobs-core's current major version**. Minor and patch
   versions are independent — each project keeps its own release cadence there, unrelated to
   pyobs-core's minor/patch.
2. While pyobs-core itself is on a pre-release/dev version (like now: `2.0.0.devN`), every project
   follows the same `.devN` suffix scheme for their own releases (e.g. `2.6.devN`, not a plain
   `2.6.0`) — this signals "not yet stable against the pyobs-core version it targets," the same way
   pyobs-core's own `.devN` suffix does. Once pyobs-core cuts a stable (non-`.dev`) release for that
   major version, every project drops the `.dev` suffix too and settles into normal semver.

This mirrors what's already established practice for the **core**-tier driver repos (pyobs-asi,
pyobs-aravis, etc.) — they've tracked pyobs-core's `2.0.0.devN` scheme all along. It now also
covers **pyobs-web-admin** explicitly: no real `pyobs-core` dependency (it talks XMPP directly),
but manually bumped to `2.0.0.dev0` on 2026-08-11 to get on the fleet-wide scheme regardless.

`web-client` (npm/TypeScript, no Python version to bump) and `polaris` (C++/CMake, same) don't
have an obvious way to apply a Python-style major-version bump — flagging this as unresolved
rather than deciding unilaterally how (or whether) a non-Python project's version should track
pyobs-core's. Worth a explicit decision later, not silently exempting them forever.

pyobs-portal complies (bumped to 2.x before the 2026-08-11 survey). pyobs-pipeline and
pyobs-dashboard-utils have real `pyobs-core` dependencies and (pipeline only) already comply on
version too — dashboard-utils still needs its own bump. pyobs-allsky-cloudcover's `pyobs-core`
dependency is currently commented out, so it's moot until that's reinstated, but the policy still
applies to its own version number regardless.

Given how much changed in the 1.x -> 2.0 rewrite (breaking API changes across the fleet, seen
repeatedly in driver fixes), a project bumping its version number alone doesn't mean it actually
works against current pyobs-core — that still needs real compatibility verification, project by
project. The version bump is a signal to chase, not a substitute for the work.

pyobs-andor, pyobs-tui, and pyobs-task-editor were all found stalled on the 1.x -> 2.0 migration
and were archived from the fleet entirely rather than fixed (see "Archived projects" above).

## Legacy major-version branches

When a project's major version bumps, the outgoing major version isn't just abandoned — it keeps
a branch named `<old-major>.x` (e.g. `1.x`) that can continue to receive its own patch/bugfix
releases and tags independently of `develop`/`main`, for however long that old major version still
needs support.

pyobs-core already does exactly this: its own `1.x` branch is still getting real patch releases
(`v1.54.4` as of 2026-07-14) in parallel with `2.0.0.devN` development on `develop`.
pyobs-portal (as pyobs-robotic-backend, before its rename) already made this jump. Any future project doing the same should create the
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
