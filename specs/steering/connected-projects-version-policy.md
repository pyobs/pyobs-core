# Connected projects that depend on pyobs-core track its major version

See `specs/steering/pyobs-project-tiers.md` for the full "connected" tier list. This policy only
applies to the subset that actually has a `pyobs-core` dependency to track compatibility against —
not the whole tier. Checked 2026-07-22:

- **pyobs-robotic-backend**: `pyobs-core>=1.54.1` in `pyproject.toml` — real dependency, policy
  applies.
- **pyobs-task-editor**: `pyobs-core>=1.46.0` in `pyproject.toml` — real dependency, policy
  applies.
- **pyobs-web-admin**: no `pyobs-core` dependency at all — it talks XMPP itself
  (`modules/ejabberd.py`), not through the pyobs-core client library. Policy does not apply.
- **pyobs-web-client**: npm project, no Python dependency whatsoever. Policy does not apply.
- **pyobs-polaris**: C++/CMake/Conan, no reference to pyobs-core anywhere in the build config
  (its own protocol client, not a pyobs-core consumer). Policy does not apply.

Versioning `web-admin`/`web-client`/`polaris` to match pyobs-core's major would be arbitrary —
there's no actual coupling for it to signal. Don't apply this policy to them just for fleet-wide
uniformity.

## The policy (for pyobs-robotic-backend and pyobs-task-editor)

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

## Current state (surveyed 2026-07-22)

pyobs-core is at `2.0.0.dev38`. Neither applicable project currently complies, and it's more than
a version-string issue:

- **pyobs-robotic-backend**: `1.6.2`, dependency pinned to `pyobs-core>=1.54.1` — predates the 2.0
  line entirely.
- **pyobs-task-editor**: `0.0.1`, dependency pinned to `pyobs-core>=1.46.0` — same.

Given how much changed in the 1.x -> 2.0 rewrite (breaking API changes across the fleet, seen
repeatedly in today's driver fixes), these two most likely don't actually work against current
pyobs-core yet. Bumping the version number alone would be misleading without first doing the real
compatibility work and verifying it. Not something to act on unprompted — each maintainer should
sign off on this individually.

## Legacy major-version branches

When a project's major version bumps, the outgoing major version isn't just abandoned — it keeps
a branch named `<old-major>.x` (e.g. `1.x`) that can continue to receive its own patch/bugfix
releases and tags independently of `develop`/`main`, for however long that old major version still
needs support.

pyobs-core already does exactly this: its own `1.x` branch is still getting real patch releases
(`v1.54.4` as of 2026-07-14) in parallel with `2.0.0.devN` development on `develop`. When
pyobs-robotic-backend or pyobs-task-editor eventually bump their major version to catch up with
pyobs-core's, they should create the equivalent `<old-major>.x` branch from their pre-bump state,
the same way, rather than just letting the old major version's history dead-end at the bump commit.

One thing to double-check rather than copy blindly when setting one of these up: pyobs-core's own
`1.x` branch has a `.github/dependabot.yml` still pointing `target-branch: "develop"` — i.e.
Dependabot updates for the 1.x line get raised against `develop`, not `1.x` itself. That may be a
leftover from before the branch split rather than an intentional choice; verify what's actually
wanted before replicating it on a new legacy branch.
