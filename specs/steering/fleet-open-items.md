# Fleet open items: open issues and plans across the pyobs fleet

Status: standing snapshot — checked on 2026-08-28 (19:40 CEST).

Fleet-wide view of what's open across the pyobs project fleet (see
`specs/steering/pyobs-project-tiers.md` for the fleet definition). This is a **derived view**, not
a source of truth:

- **Open issues**: GitHub is authoritative — re-query with `gh issue list --repo pyobs/<repo>
  --state open`.
- **Open plans**: each repo's own `specs/plans/index.md` (or `specs/index.md` for repos that keep
  their plans there) is authoritative; this doc links the docs and copies their one-line status.

**Maintenance rule: update this file whenever you open/close an issue or change a plan's status —
and remove closed items outright, never annotate them.** Only open items live here.

Repos: the whole pyobs fleet.

## Open issues (15, checked 2026-08-28 19:40 CEST)

One row per issue — same layout for every repo.

| Repo | # | Title | Notes |
|---|---|---|---|
| pyobs-core | [#825](https://github.com/pyobs/pyobs-core/issues/825) | Robotic module widgets: `IRobotic` (executor) + `IRoboticScheduler` (planner) interfaces and GUI widgets | design doc `irobotic.md` below (*proposed*); no plan yet |
| pyobs-core | [#824](https://github.com/pyobs/pyobs-core/issues/824) | `_retry_delay` overflows after 1024 attempts and permanently kills the event subscription | *bug, assigned: thusser* — cap applied after exponentiation, so attempt ≥ 1024 raises `OverflowError` (reported on 2.0.2); fix: cap the exponent before computing; plan `2026-08-28-precreate-pubsub-nodes.md` below (node pre-creation + retry hardening) |
| pyobs-core | [#823](https://github.com/pyobs/pyobs-core/issues/823) | Centralized authorization via Keycloak groups/roles (no per-service activation) | design + plan proposed, see plans below (ADR `0014`) |
| pyobs-core | [#819](https://github.com/pyobs/pyobs-core/issues/819) | Proposal: additive interface versioning (`IDome`, `IDomeV2`, ...) | design doc landed 2026-08-28 and sanity-checked against `develop`; no plan yet |
| pyobs-core | [#739](https://github.com/pyobs/pyobs-core/issues/739) | Record installed pyobs package versions in FITS headers | *enhancement* — per-package version keywords; approach undecided |
| pyobs-brot | [#61](https://github.com/pyobs/pyobs-brot/issues/61) | `set_offsets_altaz` times out (120s) repeatedly during autoguiding on MONET South | *bug, assigned: thusser* — three consecutive settle-wait timeouts during a 2026-08-24 autoguiding run on monets1m2; needs mount-side telemetry/drive-fault investigation |
| pyobs-brot | [#60](https://github.com/pyobs/pyobs-brot/issues/60) | Bump astropy pin to allow 8.x | *assigned: thusser* — `astropy<8` pin forces a downgrade alongside astropy-8 packages (e.g. in the south/monet portal image) |
| pyobs-gui | [#154](https://github.com/pyobs/pyobs-gui/issues/154) | Add generic `IStructuredConfig` widget — schema-driven form auto-built from `ConfigSchema` | *enhancement* — one generic widget covers every `IStructuredConfig` module (schema-driven editors + live `ConfigAppliedState` + `set_config()`); plan `2026-08-28-structuredconfig-widget.md` below (*proposed*) |
| pyobs-gui | [#150](https://github.com/pyobs/pyobs-gui/issues/150) | Main widgets vs. sidebar widgets — automatic tab pages for multi-widget modules | *assigned: thusser* — split widget concept into main vs. sidebar categories; affects page assembly; draft plan `2026-08-28-gui-main-vs-sidebar-widgets.md` (pyobs-gui specs, below) |
| pyobs-portal | [#119](https://github.com/pyobs/pyobs-portal/issues/119) | Update `get_module_classes()` for fleet-aggregated `api_module_classes` response shape | follow-up to pyobs-web-admin #68 — portal's `pyobs_portal/api/webadmin.py` expects the flat shape the fleet-aggregated endpoint will replace |
| pyobs-portal | [#116](https://github.com/pyobs/pyobs-portal/issues/116) | Add instrument config app for script builder (camera/telescope capabilities) | *assigned: thusser* — static instrument capability data so the script builder works without live modules |
| pyobs-web-admin | [#74](https://github.com/pyobs/pyobs-web-admin/issues/74) | Add fullscreen button for logs | *assigned: thusser* — both log views render at a fixed height with no enlarge option |
| pyobs-web-admin | [#68](https://github.com/pyobs/pyobs-web-admin/issues/68) | `api_module_classes` has no fleet-aggregating counterpart (external callers only see one host) | *bug* — design + work-plan live in the issue body itself (no separate plan file); not yet implemented; downstream update tracked as pyobs-portal #119 |
| pyobs-weather | [#6](https://github.com/pyobs/pyobs-weather/issues/6) | Historic data | *enhancement* |
| pyobs-astrometry | [#1](https://github.com/pyobs/pyobs-astrometry/issues/1) | No version tracking (no pyproject.toml) | *assigned: thusser* — nothing to tell what version is deployed; minimal `pyproject.toml` (or `VERSION` file) wanted |

## Open plans

### pyobs-core `specs/plans/`

- [2026-07-27-gui-widget-plugins-and-packaging.md](../plans/2026-07-27-gui-widget-plugins-and-packaging.md) —
  *draft* (pyobs-gui). Widget plugin mechanism + `pyside6-deploy` packaging; loading mechanism
  decided + spiked, widget-selection mechanism still open.
- [2026-07-29-gui-telescopewidget-layout.md](../plans/2026-07-29-gui-telescopewidget-layout.md) —
  *proposed* (pyobs-gui). `TelescopeWidget` width-floor investigation with candidate fixes.
- [2026-08-23-iag50-pyobs-core-2x-migration.md](../plans/2026-08-23-iag50-pyobs-core-2x-migration.md) —
  *in progress* (pyobs-iag50, IAG-internal). `1.x` branch cut, `develop` reset to
  `2.0.0.dev0`/`pyobs-core>=2.0.0.dev93`; actual code migration (grid-API rewrite, `self.proxy()`
  async-context-manager change, missing-await fixes) not yet done, three open questions need
  Tim's input.
- [2026-08-28-shared-authz-keycloak.md](../plans/2026-08-28-shared-authz-keycloak.md) —
  *proposed* (#823). Centralized authorization: Keycloak groups/roles become the source of truth;
  services gate on token claims instead of per-service `is_active` activation (design:
  `specs/design/shared-authz-keycloak.md`, ADR `0014`; Repos: pyobs-auth, pyobs-archive,
  pyobs-portal, pyobs-web-admin).
- [2026-08-28-observation-portal-keycloak-auth.md](../plans/2026-08-28-observation-portal-keycloak-auth.md) —
  *proposed* (observation-portal, pyobs-auth). Attach observation-portal (MONET fork) to Keycloak
  as a `pyobs-auth` client, additive next to local username/password auth; supersedes Section 0 of
  the 2026-08-12 shared-auth plan.
- [2026-08-28-precreate-pubsub-nodes.md](../plans/2026-08-28-precreate-pubsub-nodes.md) — *proposed*
  (#824). Pre-create pubsub event/state nodes at module startup (XEP-0060 `create_node`) so
  subscriptions can land before the first publish; plus #824 retry hardening (`_retry_delay`
  exponent clamp, stuck-key cleanup in both retry loops).

### Design docs still *proposed*

- [gui-standalone-binary.md](../design/gui-standalone-binary.md) — umbrella for the compiled
  pyobs-gui binary; login pieces done, widget plugin/selection + real plugin smoke test still open.
- [interface_versioning.md](../design/interface_versioning.md) — additive interface versioning
  (`IDome`, `IDomeV2`, ...) (#819). Sanity-checked against `develop` 2026-08-28 (MRO/diamond,
  registration, discovery, wire round-trip all verified); gaps recorded before a plan; no plan yet.
- [irobotic.md](../design/irobotic.md) — `IRobotic` (executor) / `IRoboticScheduler` (planner)
  interfaces plus `RoboticWidget` / `ScheduleWidget` in pyobs-gui (#825). Proposed; no plan yet.
- [shared-authz-keycloak.md](../design/shared-authz-keycloak.md) — centralized authorization via
  Keycloak groups/roles (#823). Proposed; decision recorded in ADR `0014`; plan
  `2026-08-28-shared-authz-keycloak.md` above.

### Sibling repos

One line per plan — same layout for every repo.

- **pyobs-gui** — [2026-08-28-gui-main-vs-sidebar-widgets.md](../../pyobs-gui/specs/2026-08-28-gui-main-vs-sidebar-widgets.md) —
  main vs. sidebar widget split, automatic tab pages for multi-widget modules (#150) (*draft*)
- **pyobs-gui** — [2026-08-28-structuredconfig-widget.md](../../pyobs-gui/specs/2026-08-28-structuredconfig-widget.md) —
  generic schema-driven `IStructuredConfig` form widget (#154) (*proposed*)
- **pyobs-web-client** — [acl-aware-shell-forms](../../pyobs-web-client/specs/plans/acl-aware-shell-forms.md) —
  ACL-aware Shell forms (*proposed*)
- **pyobs-web-client** — [auxiliary-interface-widgets](../../pyobs-web-client/specs/plans/auxiliary-interface-widgets.md) —
  auxiliary interface widgets (attach-or-standalone) (*proposed*)
- **pyobs-web-client** — [idatasequence](../../pyobs-web-client/specs/plans/idatasequence.md) —
  `IDataSequence` support ("grab N images") (*proposed*)
- **pyobs-web-client** — [rpc-fault-call-id](../../pyobs-web-client/specs/plans/rpc-fault-call-id.md) —
  surface `call_id` on RPC faults (*proposed*)
- **pyobs-web-client** — [struct-typed-command-params](../../pyobs-web-client/specs/plans/struct-typed-command-params.md) —
  `struct<Name>`-typed command params (*blocked on upstream*)
- **pyobs-web-client** — [telescope-page](../../pyobs-web-client/specs/plans/telescope-page.md) —
  telescope page for `ITelescope` modules (*proposed*)
- **pyobs-web-client** — [vfs-token-auth](../../pyobs-web-client/specs/plans/vfs-token-auth.md) —
  VFS endpoint auth (Basic Auth → Bearer token) (*proposed, unblocked — the pyobs-core release
  it depended on has shipped; pyobs-web-client's own `specs/plans/index.md` blurb hasn't caught
  up yet*)
