# The pyobs project fleet: core, connected, and internal projects

pyobs-core doesn't live alone — a fleet of sibling repos (mostly hardware drivers, plus a few
GUIs/backends) depend on it and need to stay compatible with it. When doing anything fleet-wide
(surveying for a bug pattern across repos, checking who's affected by a pyobs-core API change,
deciding what needs a compatibility pass before a pyobs-core release), use this list rather than
guessing from whatever happens to be checked out locally.

## Core projects

Actively maintained, expected to track pyobs-core closely, first candidates for any fleet-wide
check or migration:

- pyobs-alpaca
- pyobs-andor
- pyobs-aravis
- pyobs-asi
- pyobs-brot
- pyobs-core
- pyobs-fli
- pyobs-flipro
- pyobs-gemini
- pyobs-gui
- pyobs-sbig
- pyobs-tis
- pyobs-tui
- pyobs-v4l
- pyobs-zaber
- pyobs-zwoeaf

## Connected projects

Depend on pyobs-core/the core projects but sit a layer further out (web/UI clients, task
scheduling/authoring, not drivers):

- pyobs-polaris
- pyobs-robotic-backend
- pyobs-task-editor
- pyobs-web-admin
- pyobs-web-client

## IAG internal projects

Specific to IAG's own telescopes/instruments, not general-purpose drivers:

- pyobs-iag50
- pyobs-iagvt
- pyobs-monet
- pyobs-monti

## What's deliberately not on this list

Everything else in the `pyobs` GitHub org (`pyobs-weather`, `pyobs-dashboard-utils`,
`pyobs-allsky-cloudcover`, `pyobs.github.io`, `pyobs-astrometry`, `pyobs-archive`, ...) exists but
isn't part of the actively-maintained fleet by default. Don't assume they're in scope for a
fleet-wide pass unless asked explicitly.

Note: `pyobs-celestron` was removed from the GitHub org entirely (2026-07-22) — it was an empty
scaffold (one commit, a single unimplemented stub class), not an active project worth tracking
here.

Note: `pyobs-pilar` is archived on GitHub (2026-07-22) — real, substantial code and history, but
orphaned once the matching hardware was retired. Not a candidate for fleet-wide passes; unarchive
first if that hardware ever comes back.

## See also

- `specs/steering/fleet-tooling-consistency.md` — the lint/type-check/dependabot baseline every
  core+connected repo should have.
- `specs/steering/connected-projects-version-policy.md` — how connected-tier versions should
  relate to pyobs-core's, and the legacy-branch convention for outgoing major versions.
