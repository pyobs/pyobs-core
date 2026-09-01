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

## Open issues (16, checked 2026-09-01)

One row per issue — same layout for every repo.

| Repo | # | Title | Notes |
|---|---|---|---|
| pyobs-core | [#838](https://github.com/pyobs/pyobs-core/issues/838) | `DummyCamera` exposures complete but contain no visible stars: Moffat2D amplitude is never mapped | *bug* — follow-up to #829; `_simulate_image`'s `params_map` maps `x_0`/`y_0` but not `amplitude`, so `make_model_image` renders every source at amplitude 1.0, invisible under the noise floor; the Gaia-flux column from the sources table is never used. Fix is mapping `amplitude` (from flux) in `params_map`; open question left to us: total flux vs. peak value |
| pyobs-core | [#837](https://github.com/pyobs/pyobs-core/issues/837) | A child module's `vfs` config is silently replaced by the parent's under `MultiModule` | *bug* — `Object.get_object` (`pyobs/object.py`) checks `config_or_object_get_param(config, "_vfs")` (underscore) but YAML configs key the constructor param `vfs` (no underscore), so a child's own `vfs`/`timezone`/`observer` is never detected as already-set and gets overwritten by the parent's. 10-line repro in the issue. Workaround: define `vfs` at the `MultiModule` top level only |
| pyobs-core | [#832](https://github.com/pyobs/pyobs-core/issues/832) | Dark masters per exposure time: match science frames by exptime, scale only a reference (600s) dark | *assigned: thusser* — reduction half of #831; scaling-policy question resolved by ADR `0015-dark-master-strict-exptime-matching-reference-scale-down-only.md` (strict default, reference scales down only); plan `2026-09-01-per-exptime-dark-masters.md` below (*proposed*); pyobs-pipeline#13 is the downstream consumer of the new `Calibration`/`Reduction` config knobs + `MasterCalibCreated.exptime` |
| pyobs-core | [#831](https://github.com/pyobs/pyobs-core/issues/831) | Take morning darks at the exposure times used for science frames during the night | *assigned: thusser* — robotic/observing half (reduction half is #832); plan `2026-09-01-morning-darks-match-science-exptimes.md` below (*proposed*) |
| pyobs-core | [#819](https://github.com/pyobs/pyobs-core/issues/819) | Proposal: additive interface versioning (`IDome`, `IDomeV2`, ...) | design doc landed 2026-08-28 and sanity-checked against `develop`; no plan yet |
| pyobs-core | [#739](https://github.com/pyobs/pyobs-core/issues/739) | Record installed pyobs package versions in FITS headers | *enhancement* — per-package version keywords; approach undecided |
| pyobs-pipeline | [#13](https://github.com/pyobs/pyobs-pipeline/issues/13) | Support per-exposure-time dark masters: config knobs + exposure time in period UI | *enhancement, assigned: thusser* — app-side support for pyobs-core #831/#832: builder form fields for the new `Calibration`/`Reduction` options, exposure time shown in the period-detail calibs list; blocked on a pyobs-core rev containing #831/#832 (pin bump or temporary editable-path override) |
| pyobs-brot | [#61](https://github.com/pyobs/pyobs-brot/issues/61) | `set_offsets_altaz` times out (120s) repeatedly during autoguiding on MONET South | *bug, assigned: thusser* — three consecutive settle-wait timeouts during a 2026-08-24 autoguiding run on monets1m2; needs mount-side telemetry/drive-fault investigation |
| pyobs-brot | [#60](https://github.com/pyobs/pyobs-brot/issues/60) | Bump astropy pin to allow 8.x | *assigned: thusser* — pin (`astropy<8,>=7.0.1`) forces a downgrade when installed alongside pyobs-portal (locked to `astropy==8.0.1`); on south/monet's portal image, `uv run`'s re-sync undoes the downgrade on every container start (multi-minute startup tax, re-fetches astropy over the network). Needs test-suite check before widening to `<9` |
| pyobs-gui | [#154](https://github.com/pyobs/pyobs-gui/issues/154) | Add generic `IStructuredConfig` widget — schema-driven form auto-built from `ConfigSchema` | *enhancement* — one generic widget covers every `IStructuredConfig` module (schema-driven editors + live `ConfigAppliedState` + `set_config()`); plan `2026-08-28-structuredconfig-widget.md` below (*proposed*) |
| pyobs-gui | [#150](https://github.com/pyobs/pyobs-gui/issues/150) | Main widgets vs. sidebar widgets — automatic tab pages for multi-widget modules | *assigned: thusser* — split widget concept into main vs. sidebar categories; affects page assembly; draft plan `2026-08-28-gui-main-vs-sidebar-widgets.md`, revised 2026-09-01 (`sidebar_preferred` promotion rule, universal sidebar container, `paired_sidebar_widget`); follow-up plan `2026-09-01-gui-video-widget-split.md` (both pyobs-gui specs, below) |
| pyobs-portal | [#116](https://github.com/pyobs/pyobs-portal/issues/116) | Add instrument config app for script builder (camera/telescope capabilities) | *assigned: thusser* — static instrument capability data so the script builder works without live modules |
| pyobs-web-admin | [#74](https://github.com/pyobs/pyobs-web-admin/issues/74) | Add fullscreen button for logs | *assigned: thusser* — both log views render at a fixed height with no enlarge option |
| pyobs-archive | [#57](https://github.com/pyobs/pyobs-archive/issues/57) | Consider a Keycloak-role-synced archive-admin flag (deferred from #56) | |
| pyobs-weather | [#6](https://github.com/pyobs/pyobs-weather/issues/6) | Historic data | *enhancement* |
| pyobs-astrometry | [#1](https://github.com/pyobs/pyobs-astrometry/issues/1) | No version tracking (no pyproject.toml) | *assigned: thusser* — nothing to tell what version is deployed; minimal `pyproject.toml` (or `VERSION` file) wanted |

## Open plans

### pyobs-core `specs/plans/`

- [2026-09-01-morning-darks-match-science-exptimes.md](../plans/2026-09-01-morning-darks-match-science-exptimes.md) —
  *proposed* (#831). Archive API needs an `exptime` field/filter (`FrameInfo`, `PyobsArchive`,
  `LocalArchive`), a helper to derive the previous night's science exposure times, and a
  `DarkBiasScript` option to take darks at each one.
- [2026-09-01-per-exptime-dark-masters.md](../plans/2026-09-01-per-exptime-dark-masters.md) —
  *proposed* (#832, depends on #831 above). Per-exptime master darks (filename/cache/progress
  carry `exptime`), match-or-scale-reference-only-or-error policy at calibration time per ADR
  `0015`.
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
  *proposed* (observation-portal, pyobs-auth; revised 2026-08-31 — see "Direction change").
  Attach observation-portal (MONET fork) to Keycloak as a `pyobs-auth` client, additive next to
  local username/password auth; supersedes Section 0 of the 2026-08-12 shared-auth plan.

### Design docs still *proposed*

- [gui-standalone-binary.md](../design/gui-standalone-binary.md) — umbrella for the compiled
  pyobs-gui binary; login pieces done, widget plugin/selection + real plugin smoke test still open.
- [interface_versioning.md](../design/interface_versioning.md) — additive interface versioning
  (`IDome`, `IDomeV2`, ...) (#819). Sanity-checked against `develop` 2026-08-28 (MRO/diamond,
  registration, discovery, wire round-trip all verified); gaps recorded before a plan; no plan yet.

### Sibling repos

One line per plan — same layout for every repo.

- **pyobs-gui** — [2026-08-28-gui-main-vs-sidebar-widgets.md](../../pyobs-gui/specs/2026-08-28-gui-main-vs-sidebar-widgets.md) —
  main vs. sidebar widget split, automatic tab pages for multi-widget modules (#150) (*draft,
  revised 2026-09-01*)
- **pyobs-gui** — [2026-09-01-gui-video-widget-split.md](../../pyobs-gui/specs/2026-09-01-gui-video-widget-split.md) —
  split `VideoWidget` into a main widget + paired sidebar widget, follow-up to the above (#150 D6)
  (*draft*)
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
