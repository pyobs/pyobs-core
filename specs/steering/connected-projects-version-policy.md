# Connected projects track pyobs-core's major version

See `specs/steering/pyobs-project-tiers.md` for which repos are "connected" tier
(pyobs-polaris, pyobs-robotic-backend, pyobs-task-editor, pyobs-web-admin, pyobs-web-client).

## The policy

1. A connected project's **major version must match pyobs-core's major version** it was built
   against/is compatible with. Minor and patch versions are independent — each project keeps its
   own release cadence there, unrelated to pyobs-core's minor/patch.
2. While pyobs-core itself is on a pre-release/dev version (like now: `2.0.0.devN`), connected
   projects tracking that major version follow the same `.devN` suffix scheme for their own
   releases (e.g. `2.6.devN`, not a plain `2.6.0`) — this signals "not yet stable against the
   pyobs-core version it targets," the same way pyobs-core's own `.devN` suffix does. Once
   pyobs-core cuts a stable (non-`.dev`) release for that major version, connected projects drop
   the `.dev` suffix too and settle into normal semver.

This mirrors what's already established practice for the **core**-tier driver repos (pyobs-asi,
pyobs-aravis, etc.) — they've tracked pyobs-core's `2.0.0.devN` scheme all along. This policy
extends the same expectation to the connected tier, which hasn't been held to it so far.

## Current state (surveyed 2026-07-22)

pyobs-core is at `2.0.0.dev38`. None of the connected-tier projects currently comply:

- pyobs-robotic-backend: `1.6.2` (major 1, stable — needs major bump to 2, and a `.dev` suffix
  while pyobs-core 2.x is still in dev)
- pyobs-task-editor: `0.0.1` (major 0, stable)
- pyobs-web-admin: `1.9.1` (major 1, stable)
- pyobs-web-client: `0.0.0` (npm/`package.json`, major 0)
- pyobs-polaris: `1.0` (CMake `project(... VERSION 1.0)`, major 1 — also not a Python/uv project,
  so `do-python-release` doesn't apply to it; whatever bumps its CMake version needs to be done by
  hand or with its own tooling)

This is a policy statement, not something to act on unprompted — bumping five repos' major
versions is a real, visible change each maintainer should sign off on individually, not something
to batch through as a mechanical fleet-wide pass.

## Legacy major-version branches

When a project's major version bumps, the outgoing major version isn't just abandoned — it keeps
a branch named `<old-major>.x` (e.g. `1.x`) that can continue to receive its own patch/bugfix
releases and tags independently of `develop`/`main`, for however long that old major version still
needs support.

pyobs-core already does exactly this: its own `1.x` branch is still getting real patch releases
(`v1.54.4` as of 2026-07-14) in parallel with `2.0.0.devN` development on `develop`. When any
connected project eventually bumps its major version to catch up with pyobs-core's, it should
create the equivalent `<old-major>.x` branch from its pre-bump state, the same way, rather than
just letting the old major version's history dead-end at the bump commit.

One thing to double-check rather than copy blindly when setting one of these up: pyobs-core's own
`1.x` branch has a `.github/dependabot.yml` still pointing `target-branch: "develop"` — i.e.
Dependabot updates for the 1.x line get raised against `develop`, not `1.x` itself. That may be a
leftover from before the branch split rather than an intentional choice; verify what's actually
wanted before replicating it on a new legacy branch.
