# Fleet open items: open issues and plans across the pyobs fleet

Status: standing snapshot — checked on 2026-09-01.

Fleet-wide view of what's open across the pyobs project fleet (see
`specs/steering/pyobs-project-tiers.md` for the fleet definition). This is a **derived view**, not
a source of truth:

- **Open issues**: GitHub is authoritative — re-query with `gh issue list --repo pyobs/<repo>
  --state open`.
- **Open plans**: each repo's own `specs/plans/index.md` (or `specs/index.md` for repos that keep
  their plans there) is authoritative; this doc links the docs and copies their one-line status.

**Maintenance rule: update this file whenever you open/close an issue or change a plan's status —
and remove items outright once their fix has landed on `develop` (even if the GitHub issue stays
open pending a release to `main`), never annotate them.** Only open items live here.

Repos: the whole pyobs fleet.

## Open issues (10, checked 2026-09-01)

One row per issue — same layout for every repo.

| Repo | # | Title | Notes |
|---|---|---|---|
| pyobs-core | [#819](https://github.com/pyobs/pyobs-core/issues/819) | Proposal: additive interface versioning (`IDome`, `IDomeV2`, ...) | design doc landed 2026-08-28 and sanity-checked against `develop`; no plan yet |
| pyobs-core | [#739](https://github.com/pyobs/pyobs-core/issues/739) | Record installed pyobs package versions in FITS headers | *enhancement* — per-package version keywords; approach undecided |
| pyobs-core | [#844](https://github.com/pyobs/pyobs-core/issues/844) | Reduction: make min-frames-per-exptime-group threshold for dark masters configurable | *enhancement, assigned: thusser* — `_create_master_darks` hardcodes a minimum of 3 raw frames per exptime group; add a `min_darks_per_group` param matching the existing `min_flats`. Surfaced while closing out pyobs-pipeline #13/#14 |
| pyobs-brot | [#61](https://github.com/pyobs/pyobs-brot/issues/61) | `set_offsets_altaz` times out (120s) repeatedly during autoguiding on MONET South | *bug, assigned: thusser* — three consecutive settle-wait timeouts during a 2026-08-24 autoguiding run on monets1m2; needs mount-side telemetry/drive-fault investigation |
| pyobs-web-admin | [#79](https://github.com/pyobs/pyobs-web-admin/issues/79) | Add "update all" button to packages page | |
| pyobs-web-admin | [#74](https://github.com/pyobs/pyobs-web-admin/issues/74) | Add fullscreen button for logs | *assigned: thusser* — both log views render at a fixed height with no enlarge option |
| pyobs-archive | [#57](https://github.com/pyobs/pyobs-archive/issues/57) | Consider a Keycloak-role-synced archive-admin flag (deferred from #56) | |
| pyobs-weather | [#31](https://github.com/pyobs/pyobs-weather/issues/31) | develop is 12 commits behind master (through v1.2.0..v2.0.0.dev3) | repo-hygiene — `develop` needs merging/fast-forwarding to catch up |
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
- [2026-08-28-observation-portal-keycloak-auth.md](../plans/2026-08-28-observation-portal-keycloak-auth.md) —
  *proposed*, revised 2026-08-31 (observation-portal; see "Direction change"). Attach
  observation-portal (MONET fork) to OIDC via generic `mozilla-django-oidc` (no pyobs-auth
  dependency, upstream-submittable), config-gated via `OIDC_ENABLED`, additive next to local
  username/password auth; supersedes Section 0 of the 2026-08-12 shared-auth plan.

### Design docs still *proposed*

- [gui-standalone-binary.md](../design/gui-standalone-binary.md) — umbrella for the compiled
  pyobs-gui binary; login pieces done, widget plugin/selection + real plugin smoke test still open.
- [interface_versioning.md](../design/interface_versioning.md) — additive interface versioning
  (`IDome`, `IDomeV2`, ...) (#819). Sanity-checked against `develop` 2026-08-28 (MRO/diamond,
  registration, discovery, wire round-trip all verified); gaps recorded before a plan; no plan yet.

### Sibling repos

One line per plan — same layout for every repo.

- **pyobs-gui** — [2026-09-01-gui-video-widget-split.md](../../pyobs-gui/specs/2026-09-01-gui-video-widget-split.md) —
  split `VideoWidget` into a main widget + paired sidebar widget, D6 follow-up to the (now landed,
  see pyobs-gui's own `specs/index.md`) main-vs-sidebar-widgets plan (#150) (*draft, unblocked*)
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
