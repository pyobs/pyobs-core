# Plan: Add baseline tests to core-tier repos, then enable grouped Dependabot auto-merge

Status: implemented, closed 2026-08-19. All tasks done: baseline tests + CI + pyrefly + grouped dependabot (merged 2026-08-16, PRs #31/#36/#29/#53/#79/#32/#16/#62/#68/#10/#16/#31/#18 across the 13 repos), branch protection + allow_auto_merge (2026-08-16), and the Dependabot auto-merge workflow (2026-08-19, validated live on pyobs-alpaca#33). Closes #752.

Post-merge settings (2026-08-16): branch protection on `develop` with required status checks
(`test`, `ruff`, `pyrefly`) and `allow_auto_merge: true` applied to all 13 repos. `pyobs-tis`
was made public to unblock this (GitHub Free blocks branch protection and auto-merge on private
repos).

Resolved 2026-08-19 — option 2 (workflow) chosen and applied to all 13 repos:
`.github/workflows/dependabot-automerge.yml` added to each (commits "Enable Dependabot auto-merge
for patch/minor updates", then "Gate auto-merge on the PR author, not the event actor"). It's a
`pull_request` workflow that detects Dependabot PRs (gated on the **PR author**, not the event
actor, so a human reopening/touching a Dependabot PR still arms it), filters majors out via
`dependabot/fetch-metadata` `update-type`, and runs `gh pr merge --auto --merge` for patch/minor
only; `GITHUB_TOKEN` is granted `contents: write` + `pull-requests: write` in the workflow file.
Auto-merge then waits for the required checks (`test`/`ruff`/`pyrefly`) before merging.

Validated end-to-end 2026-08-19 on pyobs-alpaca#33 (a Dependabot ruff 0.16.2→0.16.3 patch bump):
the workflow ran and auto-merged the PR once CI was green.

The alternative (option 1, manual UI toggle) was rejected — not versionable, easy to forget on
future repos; option 2 keeps the fleet consistent and codified.
Issue: pyobs-core#752
Repos: pyobs-alpaca, pyobs-aravis, pyobs-asi, pyobs-brot, pyobs-fli, pyobs-flipro, pyobs-gemini,
pyobs-qhyccd, pyobs-sbig, pyobs-tis, pyobs-v4l, pyobs-zaber, pyobs-zwoeaf (see "Scope correction"
below for what changed from the issue's original list)

## Scope correction: drop pyobs-andor and pyobs-tui, add pyobs-qhyccd

The issue's task list includes `pyobs-andor` and `pyobs-tui`. Both were archived from the fleet on
2026-08-11 (`specs/steering/pyobs-project-tiers.md`, "Archived projects") — stalled on the 1.x →
2.0 migration, no longer tracked. The archival predates this plan by hours; the issue's list wasn't
updated to reflect it. This plan excludes both, and a comment is posted on #752 noting the
discrepancy rather than silently dropping them.

`pyobs-qhyccd` isn't in the issue's list either, despite being a core-tier camera driver with the
same Cython/vendor-SDK shape as `pyobs-fli`/`pyobs-flipro`/`pyobs-sbig`. Added to Phase 3 (see
below) rather than left as a gap.

That leaves **13 repos**: the issue's 14 minus pyobs-andor/pyobs-tui, plus pyobs-qhyccd.

## Why order matters

Auto-merge is only trustworthy once CI would actually catch a bad bump. Rolling out repo-by-repo
(per the issue's task 3) means picking an order — start where a real smoke test is cheap and
reliable to write, so the pattern gets validated on easy cases before spending time on the repos
where "import the driver module" itself requires a vendor SDK.

Surveyed each repo's dependencies (`pyproject.toml`) for what importing the top-level driver module
actually requires in a plain CI runner (no camera/mount/dome attached, no vendor SDK installed):

**Group A — pure Python, no native/vendor SDK at import time (do first):**
- `pyobs-alpaca` — HTTP wrapper (ASCOM Alpaca), only depends on `numpy` + `pyobs-core`
- `pyobs-tis` — depends on `numpy` + `pyobs-core` only
- `pyobs-gemini` — `aioserial` (pure Python serial), already migrated off Poetry, has `pyrefly.yml`
- `pyobs-zaber` — `zaber-motion` is a pip-installable pure-Python/gRPC client, no local SDK needed
- `pyobs-zwoeaf` — only `pyobs-core`; check whether the ZWO EAF backend is imported eagerly or lazily
  (if lazy, this is Group A; if the ctypes binding loads at import time, treat as Group B)
- `pyobs-v4l` — `opencv-python` is pip-installable; V4L2 device access happens at runtime
  (`open(/dev/videoN)`), not at import — should smoke-test clean in CI with no device present

**Group B — needs a system library or native SDK to import cleanly, but one that's
apt-installable or has a workaround (do second):**
- `pyobs-asi` — `zwoasi` wraps the ZWO ASI SDK via ctypes; confirm whether `zwoasi` raises on
  import when the native `.so` isn't found, or only when a camera is actually opened
- `pyobs-brot` — `pybrotlib` (custom MQTT-based lib); check whether it needs a live MQTT broker at
  import or only at connect time
- `pyobs-aravis` — needs Aravis + GenICam via GObject introspection (`gi`), not a plain pip
  dependency; likely needs `apt install libaravis-dev gir1.2-aravis-0.8` (or equivalent) in the CI
  workflow, or the smoke test needs to skip/xfail cleanly when `gi` isn't importable

**Group C — Cython extensions against a vendor camera SDK, hardest to get importing in CI
(do last, and possibly settle for less than full smoke tests):**
- `pyobs-fli` — `scikit-build` + Cython against the FLI SDK
- `pyobs-flipro` — Cython against the FLI Pro SDK
- `pyobs-sbig` — `src/` layout, likely Cython/native against the SBIG driver too (verify)

For Group C, a real "import the driver and instantiate it" smoke test may not be achievable without
the vendor SDK present on the CI runner. Acceptable fallback: test whatever pure-Python logic
exists around the extension (config parsing, `ICamera`/`IExposure` interface glue, header building)
without importing the compiled extension directly, and treat "make the compiled module importable
in CI" as a separate, explicitly deferred sub-task rather than silently skipping it.

## Baseline test pattern (define once, apply to every repo)

Per the issue: "at minimum: import/module-load smoke tests, plus real unit tests for any
non-hardware logic." Concretely, for each repo:

1. `tests/test_import.py` — import every public module under `pyobs_<name>/`, instantiate the main
   driver class with plausible constructor args (mocking the hardware connection), assert it
   satisfies the `IModule`/interface contracts it claims. This is the check that would actually
   catch "this doesn't even load" from a bad dependency bump.
2. `tests/test_*.py` for anything that isn't a hardware call — config/argument parsing, FITS header
   assembly, unit conversions, state machines, retry/backoff logic, anything with a `Mock`-able
   hardware boundary. Skip pure hardware I/O (opening a device, talking to a serial port) — that's
   out of scope per the issue.
3. Add `pytest` (and `pytest-asyncio` if the repo has async driver code, which most do) to
   `[dependency-groups] dev` in `pyproject.toml`.
4. Add `.github/workflows/pytest.yml` (or fold into an existing workflow) running `uv run pytest`.
   Match pyobs-core's own CI job shape rather than inventing a new one.

## Phase 1 — Group A (5-6 repos)

1. pyobs-alpaca
2. pyobs-tis
3. pyobs-gemini
4. pyobs-zaber
5. pyobs-zwoeaf (confirm Group A placement first — see note above)
6. pyobs-v4l

For each: write the baseline tests, confirm `uv run pytest` and `uv run pyrefly check` both pass
(note: pyobs-alpaca, pyobs-tis, pyobs-zaber, pyobs-v4l, pyobs-zwoeaf currently have no
`pyrefly.yml` either per `specs/steering/fleet-tooling-consistency.md` — adding one is in scope
alongside tests, since auto-merge should gate on both lint and type-check, not just tests). Then:

- Update `.github/dependabot.yml` to group patch/minor `uv`-ecosystem updates into one PR.
- Enable branch-protection required-status-checks for the new pytest (+ pyrefly, if newly added)
  workflows on `develop`.
- Enable GitHub auto-merge for Dependabot PRs gated on those checks, majors excluded (Dependabot
  grouping config below handles the major/minor split).

Dependabot grouping addition (on top of the existing per-repo `dependabot.yml`):

```yaml
updates:
  - package-ecosystem: "uv"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "tuesday"
    target-branch: "develop"
    groups:
      patch-and-minor:
        update-types:
          - "minor"
          - "patch"
    labels:
      - "dependencies"
```

Majors are excluded from the group by default (Dependabot only groups within the same
`update-types` bucket), so they still open individual PRs.

## Phase 2 — Group B (3 repos)

pyobs-asi, pyobs-brot, pyobs-aravis, same pattern as Phase 1, but budget extra time to determine
each repo's actual import-time dependency behavior before writing the smoke test (see Group B notes
above) rather than assuming.

## Phase 3 — Group C (4 repos)

pyobs-fli, pyobs-flipro, pyobs-sbig, pyobs-qhyccd. Added `pyobs-qhyccd` even though it's not in
#752's original task list — it's a core-tier camera driver with the same Cython/vendor-SDK shape as
the other three, and leaving it out would recreate the same "no CI coverage" gap this issue exists
to close. Start by establishing whether the vendor SDK can run in CI at all (headless/no-hardware
mode, or a stub library) — this determines whether "import the compiled extension" is achievable or
needs to be scoped out. Write whatever tests are achievable; explicitly document what's left
untested and why in each repo's test suite (a comment or short `tests/README`, not a `pyobs-core`
design doc).

## Explicitly out of scope

- Testing against real hardware — the issue scopes this to "non-hardware logic."
- Retroactively fixing the `pyobs-core` 1.x `dependabot.yml` `target-branch` quirk noted in
  `pyobs-project-tiers.md` — unrelated to this issue.

## Resolved scope questions

- pyobs-andor/pyobs-tui: dropped from scope (archived from the fleet 2026-08-11, predates this
  plan). Flagged via a comment on #752 rather than silently dropped.
- pyobs-qhyccd: added to Phase 3 (see above) rather than left as a follow-up issue.
