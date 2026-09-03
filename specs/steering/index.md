# Steering

Standing, topic-scoped contributor guidance. Only add a doc here once a real recurring convention
warrants it, not for speculative content.

- [blocking-sdk-calls-must-not-run-on-the-event-loop.md](blocking-sdk-calls-must-not-run-on-the-event-loop.md) —
  blocking vendor SDK calls must never run directly on the event loop.
- [astropy-iers-event-loop-stalls.md](astropy-iers-event-loop-stalls.md) — astropy's IERS
  auto-download can block the event loop from inside `basetelescope.py`.
- [scheduler-cpu-bound-merit-evaluation-stalls-event-loop.md](scheduler-cpu-bound-merit-evaluation-stalls-event-loop.md) —
  `OnDemandScheduler.evolve()` re-doing an uncached astropy sunset lookup blocks the event loop.
- [module-opened-fanout-stalls-event-loop.md](module-opened-fanout-stalls-event-loop.md) —
  `Module._on_module_opened`'s unthrottled per-peer fan-out on connect can saturate a single-loop
  client's event loop; confirmed on both a module (iag50) and pyobs-gui (`monet`).
- [finding-module-logs-under-pyobsd.md](finding-module-logs-under-pyobsd.md) — finding a specific
  module's logs on a `pyobsd`-managed host.
- [pyobs-project-tiers.md](pyobs-project-tiers.md) — the pyobs project fleet: core, connected, and
  internal projects.
- [fleet-tooling-consistency.md](fleet-tooling-consistency.md) — shared lint/type-check/Dependabot
  tooling baseline for GitHub-hosted core/connected projects.
- [fleet-open-items.md](fleet-open-items.md) — standing snapshot of open issues and plans across
  the fleet; update it (and remove closed items) whenever fleet-relevant status changes.
- [docs-structure-by-project-group.md](docs-structure-by-project-group.md) — shared Sphinx docs
  and README structure per repo group (driver-module/gui/web-app), with copyable skeletons in
  `docs/templates/` and per-repo current-state gaps. Hand this doc to an agent fixing one repo's
  docs.
