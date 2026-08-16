# Steering

Standing, topic-scoped contributor guidance. Only add a doc here once a real recurring convention
warrants it, not for speculative content.

- [blocking-sdk-calls-must-not-run-on-the-event-loop.md](blocking-sdk-calls-must-not-run-on-the-event-loop.md) —
  blocking vendor SDK calls must never run directly on the event loop.
- [astropy-iers-event-loop-stalls.md](astropy-iers-event-loop-stalls.md) — astropy's IERS
  auto-download can block the event loop from inside `basetelescope.py`.
- [scheduler-cpu-bound-merit-evaluation-stalls-event-loop.md](scheduler-cpu-bound-merit-evaluation-stalls-event-loop.md) —
  `OnDemandScheduler.evolve()` re-doing an uncached astropy sunset lookup blocks the event loop.
- [finding-module-logs-under-pyobsd.md](finding-module-logs-under-pyobsd.md) — finding a specific
  module's logs on a `pyobsd`-managed host.
- [pyobs-project-tiers.md](pyobs-project-tiers.md) — the pyobs project fleet: core, connected, and
  internal projects.
- [fleet-tooling-consistency.md](fleet-tooling-consistency.md) — shared lint/type-check/Dependabot
  tooling baseline for GitHub-hosted core/connected projects.
