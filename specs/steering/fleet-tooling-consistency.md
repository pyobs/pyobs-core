# Every GitHub-hosted core/connected project should share the same tooling baseline

See `specs/steering/pyobs-project-tiers.md` for which repos this applies to. This doc is about
what's expected of each of them, tooling-wise — not which repos exist.

## The baseline

Every GitHub-hosted repo in the core and connected tiers should have:

0. **`uv` as the Python build backend/package manager** — not Poetry, not plain pip/setuptools.
   `pyproject.toml` should declare `uv` (`[build-system] requires = ["uv_build>=..."]` or
   equivalent), and the repo should carry a `uv.lock`, not a `poetry.lock`/`requirements.txt`.
   Known exceptions still on Poetry as of the 2026-07-22 survey: `pyobs-andor`, `pyobs-gemini` —
   these need an actual migration (not just a Dependabot ecosystem accommodation) to get in line;
   Dependabot is configured against `pip` for them in the meantime, which is the closest
   Dependabot ecosystem to a Poetry-managed `pyproject.toml`, not a long-term fix.
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

## Current state (surveyed 2026-07-22, corrected same day)

An initial pass at this survey used a broken check (`gh api .../contents/<path> -q '.name'` on a
404 prints the literal string `"null"` to stdout, which a naive `${var:+yes}` test reads as
"non-empty, so present" — always check the command's exit status, not text content scraped from
a response that might be an error body instead of the real one). The corrected results:

- **pyobs-core, pyobs-gui**: pre-commit + ruff CI + pyrefly CI + dependabot(develop) — full
  baseline, the only two repos actually meeting it in full.
- **pyobs-alpaca, pyobs-aravis, pyobs-asi, pyobs-brot, pyobs-fli, pyobs-flipro, pyobs-sbig,
  pyobs-v4l, pyobs-zaber, pyobs-zwoeaf**: pre-commit + ruff CI, but **no `pyrefly.yml` CI job at
  all** — type checking isn't actually enforced in CI on these, only lint. Dependabot present and
  targeting `develop` on all of these except pyobs-alpaca and pyobs-brot (missing entirely there).
- **pyobs-tis**: pre-commit only, no ruff CI, no pyrefly CI. Dependabot present, targets `develop`.
- **pyobs-tui**: pre-commit only, no ruff CI, no pyrefly CI, no dependabot.
- **pyobs-andor, pyobs-gemini, pyobs-polaris, pyobs-robotic-backend, pyobs-task-editor,
  pyobs-web-admin, pyobs-web-client**: none of pre-commit/ruff CI/pyrefly CI/dependabot at all.

So the actual gap is much larger than "just Dependabot": most of the core tier is missing
`pyrefly.yml` CI entirely (lint-only, not actually type-checked in CI), and 9 repos across
core+connected have no lint/type-check pipeline of any kind. Dependabot-only fixes (this session's
initial pass) don't address that; treat it as a separate, larger follow-up.

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
