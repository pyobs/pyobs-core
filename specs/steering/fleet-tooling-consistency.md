# Every GitHub-hosted core/connected project should share the same tooling baseline

See `specs/steering/pyobs-project-tiers.md` for which repos this applies to. This doc is about
what's expected of each of them, tooling-wise — not which repos exist.

## The baseline

Every GitHub-hosted repo in the core and connected tiers should have:

1. **Lint/type-check pipeline**, matching pyobs-core's own setup exactly:
   - `.pre-commit-config.yaml` running `black` (via the `psf/black-pre-commit-mirror`) and `ruff`
     (via `astral-sh/ruff-pre-commit`).
   - `.github/workflows/ruff.yml` — CI job running `uv run ruff check <package>/`.
   - `.github/workflows/pyrefly.yml` — CI job running `uv run pyrefly check`.
2. **Dependabot** (`.github/dependabot.yml`), `uv` ecosystem, weekly schedule, and critically
   `target-branch: "develop"` — Dependabot only reads this file from the repo's *default* branch
   (`main` for most of the fleet), but the PRs it opens should still land on `develop` like every
   other change, not go straight to `main`.

The IAG-internal tier (`pyobs-iag50`, `pyobs-iagvt`, `pyobs-monet`, `pyobs-monti`) is GitLab-hosted,
not GitHub — Dependabot doesn't apply there at all (GitLab has no equivalent configured for these
repos today). The lint/type-check expectation (ruff/pyrefly/black) still applies in spirit, but via
GitLab CI (`.gitlab-ci.yml`), not GitHub Actions.

## Current state (surveyed 2026-07-22)

Lint/type-check pipeline: **already consistent everywhere** — every one of the 21 GitHub-hosted
core+connected repos already has `.pre-commit-config.yaml`, `ruff.yml`, and `pyrefly.yml`. Nothing
to fix here; re-verify this assumption before relying on it if it's been a while.

Dependabot target-branch: inconsistent. As of the survey:

- **Already correct** (`target-branch: develop`): pyobs-core, pyobs-aravis, pyobs-asi, pyobs-fli,
  pyobs-flipro, pyobs-gui, pyobs-sbig, pyobs-tis, pyobs-v4l, pyobs-zaber, pyobs-zwoeaf.
- **Missing entirely** (no `dependabot.yml` at all, so Dependabot doesn't run there in any form):
  pyobs-alpaca, pyobs-andor, pyobs-brot, pyobs-gemini, pyobs-tui, pyobs-polaris,
  pyobs-robotic-backend, pyobs-task-editor, pyobs-web-admin, pyobs-web-client.

To fix one of the "missing" repos: add `.github/dependabot.yml` on **both** `main` (or whatever the
repo's actual default branch is — check first, don't assume) and `develop`, since Dependabot only
reads the file from the default branch, but the file's own content should exist on develop too so
it doesn't look like a one-off drift next time someone diffs the branches. Content:

```yaml
version: 2
updates:
  - package-ecosystem: "uv"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "tuesday"
    target-branch: "develop"
    labels:
      - "dependencies"
```

Landing this on the default branch may require a PR rather than a direct push if that branch is
protected (several fleet repos are) — check `branches/<default>` via the API for `.protected`
first rather than assuming either way.
