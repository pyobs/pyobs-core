# CLAUDE.md

Entry points for working in this repo.

## Design history and planning

- **`specs/design/`** — living architecture/design docs, one per feature or subsystem. Kept
  around after landing (`status: implemented`), not deleted — check here before re-deriving the
  reasoning behind existing behavior.
- **`specs/plans/`** — implementation plans, checklist-style.
- **`specs/adrs/`** — short decision records for choices that had genuine considered-and-rejected
  alternatives (MADR-lite: Context, Considered Options, Decision Outcome, Consequences).
- **`specs/steering/`** — reserved for standing, topic-scoped contributor guidance (e.g. "how to
  add a new interface"), once a real recurring convention warrants its own doc. Empty for now;
  don't add speculative content here.

`docs/` is the Sphinx documentation site (`docs/source/`) — user-facing docs only, not design or
planning notes.

## Tooling

- Lint: `ruff` (config in `pyproject.toml`)
- Format: `black`
- Type checking: `pyrefly` — **not mypy**
- Tests: `pytest`. Tests marked `integration`/`xmpp` need a live ejabberd server
  (`tests/xmpp/docker-compose.yml`); everything else runs standalone.
- `check_coverage.md` — a point-in-time coverage-gap survey, not living documentation; re-run
  coverage directly rather than trusting it as current state.
