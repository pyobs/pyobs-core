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

## Open issues (19, checked 2026-09-01)

One row per issue — same layout for every repo.

| Repo | # | Title | Notes |
|---|---|---|---|
| pyobs-core | [#851](https://github.com/pyobs/pyobs-core/issues/851) | `DummyCamera` images the sky through a closed `DummyRoof` | *bug* — found on 2.1.1; the camera module has no roof reference, so nothing connects the two. Fix direction: an optional roof reference on `DummyCamera`, like the existing telescope reference, that darkens frames when the roof isn't open |
| pyobs-core | [#850](https://github.com/pyobs/pyobs-core/issues/850) | A refused slew (`AltitudeLimitError`) puts the module in ERROR state until a manual reset | *bug* — found on 2.1.1 with `DummyRaDecTelescope` via pyobs-gui; a correctly-refused slew is handled as severe, module goes to error and rejects every further command (even valid ones) until `reset_error()` |
| pyobs-core | [#849](https://github.com/pyobs/pyobs-core/issues/849) | `DummyRoof.stop_motion` always ends in IDLE, even on a parked roof | *bug* — found via the pyobs-gui roof widget on 2.1.1; stopping a parked/closed roof still reports IDLE, which reads as open. A scheduler trusting motion status to know whether the sky is available would start observing under a closed roof. Fix: derive status from `_open_percentage` instead of hardcoding IDLE |
| pyobs-core | [#848](https://github.com/pyobs/pyobs-core/issues/848) | `OnDemandScheduler` doesn't reschedule on project changes (e.g. new priorities) | *bug, assigned: thusser* — two gaps: pyobs-portal's `last_task_update` marker ignores project edits (portal-side plan + PR [#134](https://github.com/pyobs/pyobs-portal/pull/134) open), and `Scheduler._update_schedule()` compares task IDs only, not project content (core-side plan `2026-09-01-scheduler-reschedule-on-project-and-task-changes.md`, not started) (Repos: pyobs-core, pyobs-portal) |
| pyobs-core | [#846](https://github.com/pyobs/pyobs-core/issues/846) | `DarkBiasScript`: inherit archive/site from the caller instead of per-task config (like pipeline steps) | *enhancement, on hold* — mirror pyobs-pipeline's `_with_default_archive()` caller-level inheritance instead of requiring `archive`/`site` on every task with `match_science_exptimes=True` (follow-up to #831). Confirmed no existing caller-level slot holds archive+site (checked `TaskRunner`, `Object`'s location/observer, `LcoObservationArchive`'s site) — a real new injection point, not a wiring gap. Same redundancy also exists in `pyobs/robotic/utils/skyflats/priorities/archive.py`. Not required at the moment (Repos: pyobs-core, pyobs-portal, pyobs-pipeline) |
| pyobs-core | [#845](https://github.com/pyobs/pyobs-core/issues/845) | `Module._on_module_opened` crashes with unhandled `ValueError` when a peer cannot be resolved | *bug* — `Comm._resolve_proxy` raises plain `ValueError`, not `PyobsError`, so the handler's `except exc.PyobsError` doesn't catch it; logged as an unhandled exception on every such event. Regression from #669's exception-handling rollout |
| pyobs-core | [#819](https://github.com/pyobs/pyobs-core/issues/819) | Proposal: additive interface versioning (`IDome`, `IDomeV2`, ...) | design doc landed 2026-08-28 and sanity-checked against `develop`; no plan yet |
| pyobs-core | [#844](https://github.com/pyobs/pyobs-core/issues/844) | Reduction: make min-frames-per-exptime-group threshold for dark masters configurable | *enhancement, assigned: thusser* — `_create_master_darks` hardcodes a minimum of 3 raw frames per exptime group; add a `min_darks_per_group` param matching the existing `min_flats`. Surfaced while closing out pyobs-pipeline #13/#14 |
| pyobs-core | [#739](https://github.com/pyobs/pyobs-core/issues/739) | Record installed pyobs package versions in FITS headers | *enhancement* — per-package version keywords; approach undecided |
| pyobs-brot | [#61](https://github.com/pyobs/pyobs-brot/issues/61) | `set_offsets_altaz` times out (120s) repeatedly during autoguiding on MONET South | *bug, assigned: thusser* — three consecutive settle-wait timeouts during a 2026-08-24 autoguiding run on monets1m2; needs mount-side telemetry/drive-fault investigation |
| pyobs-web-admin | [#82](https://github.com/pyobs/pyobs-web-admin/issues/82) | Log views: auto-refresh destroys text selection, making it impossible to copy text | *bug* — `renderLogs()` rebuilds the whole `<pre>` via `innerHTML` every 3s tick, wiping any in-progress selection even when nothing new arrived; fix direction open (no-op guard vs. pause-on-select vs. incremental DOM) |
| pyobs-portal | [#135](https://github.com/pyobs/pyobs-portal/issues/135) | Cascade task deactivation/deletion to pending observations | *bug, assigned: thusser* — root cause behind pyobs-core#847 (fixed on the pyobs-core side via #852): deactivating/deleting a task doesn't cancel its pending observations on the portal, so they sit stale referencing a task the API no longer serves. pyobs-core's scheduler/mastermind are now resilient to this, but the stale window on every deactivation is still there until the portal cascades it |
| pyobs-portal | [#132](https://github.com/pyobs/pyobs-portal/issues/132) | Script builder: if a dropdown has only one option, preselect it as the default | *assigned: thusser* — module-ref and optional-polymorphic selects in the schema-driven forms default to blank even when there's exactly one candidate |
| pyobs-portal | [#131](https://github.com/pyobs/pyobs-portal/issues/131) | `script_tree()`: don't show modules that start with an underscore | *assigned: thusser* — `pkgutil.iter_modules` scan surfaces private `_*` modules/classes as script/provider types; no current core module hits it, but extension packages could |
| pyobs-archive | [#57](https://github.com/pyobs/pyobs-archive/issues/57) | Consider a Keycloak-role-synced archive-admin flag (deferred from #56) | |
| pyobs-weather | [#6](https://github.com/pyobs/pyobs-weather/issues/6) | Historic data | *enhancement* |
| pyobs-weather | [#33](https://github.com/pyobs/pyobs-weather/issues/33) | User management with Keycloak login | *enhancement* — prerequisite for #6, historic-data download should be logged-in-only; needs Keycloak SSO like the other web projects |
| pyobs-astrometry | [#1](https://github.com/pyobs/pyobs-astrometry/issues/1) | No version tracking (no pyproject.toml) | *assigned: thusser* — nothing to tell what version is deployed; minimal `pyproject.toml` (or `VERSION` file) wanted |
| pyobs-polaris | [#4](https://github.com/pyobs/pyobs-polaris/issues/4) | macOS binary missing from the dev2 and dev3 releases | release-artifact regression (dev1 had all three platforms); reporter's dev1 macOS build runs well on Apple Silicon, incl. against a real ZWO AM3N mount over a third-party INDI driver |

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
- [2026-09-01-instrument-capability-duration-estimates.md](../plans/2026-09-01-instrument-capability-duration-estimates.md) —
  *proposed*, no issue yet (pyobs-core, pyobs-portal). Feed pyobs-portal#133's instrument
  capability data (readout/filter-change/slew/dome-rotate times) into `Script.estimate_duration()`
  for `ImagingScript` and 4 other leaf scripts via a new `TaskData.instrument_capabilities` field;
  wires the portal's script builder and `OnDemandScheduler` (not `AstroplanScheduler`).
- [2026-09-01-scheduler-reschedule-on-project-and-task-changes.md](../plans/2026-09-01-scheduler-reschedule-on-project-and-task-changes.md) —
  *proposed* (issue #848; pyobs-core). `Scheduler._update_schedule()`'s change detection is
  task-ID-only, so a project priority change or a same-ID task content change never triggers a
  reschedule; adds project/task content-diff (mirroring `PortalTaskArchive._update()`) plus a fix
  for an assignment-order bug that overwrites `self._projects` before it could ever be compared.
  Portal-side signal fix is the separate `pyobs-portal` plan below.

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
- **pyobs-portal** — [2026-09-01-last-task-update-marker-includes-projects.md](../../pyobs-portal/specs/plans/2026-09-01-last-task-update-marker-includes-projects.md) —
  `/api/last_task_update/` only tracks `Max(Task.updated_at)`, so a `Project` edit (e.g. priority)
  never moves the marker and pyobs-core's `PortalTaskArchive` never re-polls; adds
  `Project.updated_at` (new field + migration) and folds it into the marker query (*proposed*,
  issue #848, open PR [#134](https://github.com/pyobs/pyobs-portal/pull/134))
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
