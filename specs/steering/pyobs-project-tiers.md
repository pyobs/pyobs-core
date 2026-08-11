# The pyobs project fleet: core, connected, and internal projects

pyobs-core doesn't live alone — a fleet of sibling repos (mostly hardware drivers, plus a few
GUIs/backends) depend on it and need to stay compatible with it. When doing anything fleet-wide
(surveying for a bug pattern across repos, checking who's affected by a pyobs-core API change,
deciding what needs a compatibility pass before a pyobs-core release), use this list rather than
guessing from whatever happens to be checked out locally.

## Core projects

Actively maintained, expected to track pyobs-core closely, first candidates for any fleet-wide
check or migration:

### Framework

- pyobs-core — module system, interfaces, XMPP comms, robotic scheduler (Python, uv)

### Cameras

- pyobs-andor — Andor camera driver (Python, uv)
- pyobs-aravis — Aravis/GenICam camera driver (Python, uv)
- pyobs-asi — ZWO ASI camera driver (Python, uv)
- pyobs-fli — FLI camera driver (Python, uv, Cython)
- pyobs-flipro — FLI Pro-series camera driver (Python, uv, Cython)
- pyobs-qhyccd — QHYCCD camera driver (Python, uv, Cython)
- pyobs-sbig — SBIG camera driver (Python, uv, Cython)
- pyobs-tis — The Imaging Source camera driver (Python, uv)
- pyobs-v4l — Video4Linux camera driver (Python, uv)

### Mounts, domes, and focusers

- pyobs-alpaca — ASCOM Alpaca wrapper, a generic device wrapper over HTTP (Python, uv)
- pyobs-brot — telescopes, domes, and roll-off roofs via BROTlib/MQTT (Python, uv)
- pyobs-gemini — Optec Gemini rotator/focuser (Python, uv)
- pyobs-zaber — Zaber motion-control stages (Python, uv)
- pyobs-zwoeaf — ZWO electronic autofocuser (Python, uv)

### User interfaces

- pyobs-gui — desktop GUI (Python, uv, PySide6/Qt6)
- pyobs-polaris — clean-room desktop client modeled on pyobs-gui (C++20, CMake, Qt6)
- pyobs-tui — terminal UI (Python, uv, Textual)
- pyobs-web-client — browser client (TypeScript, npm, Vue 3)

## Connected projects

Depend on pyobs-core/the core projects but sit a layer further out (web/UI clients, task
scheduling/authoring, not drivers):

### Task scheduling and operations

- pyobs-robotic-backend — REST API + web frontend for tasks/projects/observations/scheduling
  (Python, uv, Django + DRF)
- pyobs-task-editor — desktop app for authoring tasks (Python, uv, PySide6/Qt6)
- pyobs-web-admin — start/stop/restart modules, tail logs, edit configs, from a browser
  (Python, uv, Django)

### Data processing and archiving

- pyobs-archive — LCO-style image archive (Python, uv, Django)
- pyobs-astrometry — astrometry.net web service for plate solving; wraps the C astrometry.net
  toolchain (Python, Flask, no uv/lockfile — plain script + Dockerfile)
- pyobs-pipeline — reduction-pipeline monitoring/configuration (Python, uv, Django)

### Site and environment monitoring

- pyobs-allsky-cloudcover — cloud-cover detection from allsky images, writes to InfluxDB
  (Python + Rust, Poetry/Cargo — not uv)
- pyobs-weather — weather-station aggregator with "is it good?" rules (Python, uv, Django)

### Dashboards

- pyobs-dashboard-utils — modules for building a dashboard (Python, uv)

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

## See also

- `specs/steering/fleet-tooling-consistency.md` — the lint/type-check/dependabot baseline every
  core+connected repo should have.
- `specs/steering/connected-projects-version-policy.md` — how connected-tier versions should
  relate to pyobs-core's, and the legacy-branch convention for outgoing major versions.
