# Fleet open items: open issues and plans across the pyobs fleet

Status: standing snapshot — last checked 2026-09-10.

<details>
<summary>Changelog (most recent first)</summary>

- **2026-09-10**: pyobs-web-client #40-#47 all verified **fixed and released** (`v0.8.0`/`v0.9.0`)
  against the pulled `develop` (`b60eacf`) — commits `1a7e834`/`1e3fc34`/`7327f91` (#40, #42),
  `af58992` (#41, #43), `af4d0b5` (#44), `701ae13` (#45), `6e78ea0` (#46), `5b302aa` (#47) —
  dropped per the maintenance rule (GitHub issues stay open pending closure). #48 (auth for
  embedding other pyobs apps) and #49 (don't drop the XMPP connection on brief
  background/foreground) verified still open in code: no app-lifecycle/`appStateChange` handling
  and no embedding-auth design yet.
- **2026-09-09**: added pyobs-core #895 (Mastermind reschedule on a late-skipped start window),
  #891 (weather module never backs off on repeated station failures); pyobs-brot #68 (MQTT client
  no auto-reconnect); pyobs-pipeline #17 (Keycloak login); pyobs-polaris #6 (CameraView renders
  nothing — looks for `ICamera` in the stateful list); pyobs-web-client #44-#49 (six new issues:
  form field labels, confirm-exit swipe, connection-label leak, reconnect error message, auth for
  embedding other pyobs apps, background/foreground connection drop). Dropped pyobs-web-client #33
  (closed) and its `auxiliary-interface-widgets` plan (done 2026-09-08). Added plans: pyobs-web-client
  `2026-09-09-safe-area-insets.md` (*proposed*), pyobs-portal
  `2026-09-02-instrument-capability-estimate-duration-endpoint.md` (*proposed*).
- **2026-09-08**: pyobs-core#866 confirmed closed (closed 2026-09-04, same day as the prior
  check — missed being dropped then). pyobs-core#884 opened — mobile app (Android/iOS)
  design-and-reasoning issue, deliberately kept as discussion rather than a `specs/design/`
  doc/plan yet. `2026-09-04-camera-filterwheel-descriptive-fields.md` merged same day it was
  written (pyobs-core PR #882, pyobs-portal PR #152) — never needed adding here. pyobs-web-client
  shipped three of the six previously-tracked plans (`acl-aware-shell-forms`, `telescope-page`,
  `vfs-token-auth` — all now **done**) and opened a new one,
  `2026-09-06-mobile-first-redesign.md` (**in progress**: Phase 1 done — Dashboard,
  Connections/Login, ModulePage drill-down migrated; per-widget compact visual passes
  outstanding). Five new pyobs-web-client issues (#33, #40, #41, #42, #43), all filed
  2026-09-08 against `CameraView.vue`/`ParamForm.vue`, look like follow-ons surfacing from that
  redesign work — added to the issues table since pyobs-web-client wasn't being tracked there at
  all before.
- **2026-09-04**: pyobs-weather#6 (historic data download) rescoped to a login-gated CSV export
  now that Keycloak login exists, implemented and merged to `develop` via pyobs-weather#38
  (`767dec9`), plan doc `pyobs-weather/specs/plans/2026-09-04-historic-data-csv-export.md` —
  dropped per the maintenance rule (issue stays open pending release to `master`, this repo's
  default branch).
- **2026-09-04**: pyobs-core#858 rescoped — review decided against the live-telescope-position
  piece entirely ("no observed operational symptom motivating this"), kept only the mean-distance
  dome-rotate-time half (`specs/plans/2026-09-04-first-task-slew-rotate-distance.md`). Plain-roof
  capability field split out to #877, closed same day
  (`specs/plans/2026-09-04-roof-open-close-capability.md`). Both pieces landed on `develop`
  (`2dd30a1b`, PR #878 / pyobs-portal#149) and are released — #858 dropped per the maintenance
  rule (GitHub issue stays open pending closure). #859 flagged as likely moot: it's a follow-on to
  the live-position idea #858 just decided not to build; left open pending Tim's call rather than
  closed unilaterally.
- **2026-09-04**: pyobs-core#871 fix merged to `develop` via PR #876 (`a9ed16fe`) per
  `specs/plans/2026-09-03-comm-unregister-event-task-cancellation.md`, dropped per the maintenance
  rule (issue stays open pending release to `main`).
- **2026-09-03**: pyobs-web-admin#89 closed, dropped. #831/#832 landed on `develop` via PR
  #840/#842, dropped per the maintenance rule (issues stay open pending release to `main`).
  observation-portal-keycloak-auth plan dropped — implemented and deployed for MONET.
  pyobs-portal#141 and pyobs-weather#35 closed. pyobs-core#871 and pyobs-web-admin#89 opened (new
  repo in this table). pyobs-portal's
  `2026-09-02-instrument-capability-estimate-duration-endpoint.md` added then dropped same day —
  implemented/closed (`e9f3f55`/`b3f6a59`). pyobs-core#849 closed — fix landed `f95da2c6`
  2026-09-01, issue just hadn't been closed. pyobs-core#861 closed — fixed in pyobs-web-client,
  landed `7fa5061`. pyobs-archive#57 closed as won't-do — archive admin surface stays manual, no
  Keycloak-synced role. pyobs-portal#143 fixed and closed — dashboard timeline forces UTC axis
  labels via vis-timeline's moment hook, landed `9cf7d1d`. pyobs-core#872 opened — audit fleet for
  missing FITS header fields (follow-up to #739), then closed same day — implemented and released
  fleet-wide (pyobs-core 2.6.1 + 15 sibling repos) per
  `specs/plans/2026-09-03-fits-header-audit-followthrough.md`. pyobs-gui#150 closed —
  main-vs-sidebar-widgets plan released `v2.3.0`, dropped; pyobs-gui's video-widget-split plan (D6
  follow-up) also landed and released in the same `v2.3.0`, dropped. pyobs-core#863 restricted to
  pyobs-weather-only scope, implemented client-side and closed — landed on pyobs-weather `develop`
  `a6dcb65`, see pyobs-weather `specs/adrs/0001-per-theme-color-adaptation-stays-client-side.md`.
  pyobs-core#739 closed — implemented in `b197528c` per
  `specs/plans/2026-09-03-package-versions-fits-header.md`.

</details>

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

## Open issues (12, checked 2026-09-10)

One row per issue — same layout for every repo.

| Repo | # | Title | Notes |
|---|---|---|---|
| pyobs-core | [#895](https://github.com/pyobs/pyobs-core/issues/895) | Mastermind should trigger a reschedule when a task's start window is skipped for lateness | |
| pyobs-core | [#891](https://github.com/pyobs/pyobs-core/issues/891) | Weather module never backs off on repeated station connection failures | |
| pyobs-core | [#884](https://github.com/pyobs/pyobs-core/issues/884) | Mobile app for pyobs (Android/iOS): XMPP over WebSocket + shared TS core with pyobs-web-client | *proposal, discussion-stage* — deliberately kept as the design-and-reasoning record rather than a `specs/design/` doc + plan yet |
| pyobs-core | [#846](https://github.com/pyobs/pyobs-core/issues/846) | `DarkBiasScript`: inherit archive/site from the caller instead of per-task config (like pipeline steps) | *enhancement, on hold* — mirror pyobs-pipeline's `_with_default_archive()` caller-level inheritance instead of requiring `archive`/`site` on every task with `match_science_exptimes=True` (follow-up to #831). Confirmed no existing caller-level slot holds archive+site (checked `TaskRunner`, `Object`'s location/observer, `LcoObservationArchive`'s site) — a real new injection point, not a wiring gap. Same redundancy also exists in `pyobs/robotic/utils/skyflats/priorities/archive.py`. Not required at the moment (Repos: pyobs-core, pyobs-portal, pyobs-pipeline) |
| pyobs-core | [#819](https://github.com/pyobs/pyobs-core/issues/819) | Proposal: additive interface versioning (`IDome`, `IDomeV2`, ...) | design doc landed 2026-08-28 and sanity-checked against `develop`; no plan yet |
| pyobs-core | [#859](https://github.com/pyobs/pyobs-core/issues/859) | Track last-scheduled-task position through `OnDemandScheduler` for slew-distance estimates beyond the first task | *enhancement, likely moot* — this built on #858's live-telescope-position piece, which #858's own review decided against building ("no observed operational symptom motivating this"); worth closing or re-scoping, flagging for Tim rather than acting unilaterally |
| pyobs-brot | [#68](https://github.com/pyobs/pyobs-brot/issues/68) | MQTT client does not auto-reconnect after disconnect | |
| pyobs-brot | [#61](https://github.com/pyobs/pyobs-brot/issues/61) | `set_offsets_altaz` times out (120s) repeatedly during autoguiding on MONET South | *bug, assigned: thusser* — three consecutive settle-wait timeouts during a 2026-08-24 autoguiding run on monets1m2; needs mount-side telemetry/drive-fault investigation |
| pyobs-pipeline | [#17](https://github.com/pyobs/pyobs-pipeline/issues/17) | Add Keycloak login | |
| pyobs-polaris | [#6](https://github.com/pyobs/pyobs-polaris/issues/6) | Camera page renders nothing: `CameraView` looks for `ICamera` in the stateful list, but `ICamera` has no state | |
| pyobs-web-client | [#49](https://github.com/pyobs/pyobs-web-client/issues/49) | Don't drop XMPP connection on brief background/foreground | *needs design* — no app-lifecycle/`appStateChange` handling in code yet; decide a grace period and how it interacts with mobile OS background-network limits |
| pyobs-web-client | [#48](https://github.com/pyobs/pyobs-web-client/issues/48) | Design auth for embedding other pyobs apps (web-admin, portal, weather, pipeline) | *design-stage* — leaning SSO via Keycloak; open risk: a Capacitor webview doesn't share cookies with the system browser, may need an in-app browser tab for the auth hop |

## Open plans

### pyobs-core `specs/plans/`

- [2026-07-27-gui-widget-plugins-and-packaging.md](../plans/2026-07-27-gui-widget-plugins-and-packaging.md) —
  *draft* (pyobs-gui). Widget plugin mechanism + `pyside6-deploy` packaging; loading mechanism
  decided + spiked, widget-selection mechanism still open.
- [2026-07-29-gui-telescopewidget-layout.md](../plans/2026-07-29-gui-telescopewidget-layout.md) —
  *proposed* (pyobs-gui). `TelescopeWidget` width-floor investigation with candidate fixes.
- [2026-08-23-iag50-pyobs-core-2x-migration.md](../plans/2026-08-23-iag50-pyobs-core-2x-migration.md) —
  *in progress* (pyobs-iag50, IAG-internal). `1.x` branch cut, `develop` reset to `2.0.0.dev0`;
  actual code migration (grid-API rewrite, `self.proxy()` async-context-manager change,
  missing-await fixes) not yet done, three open questions need Tim's input.

### Design docs still *proposed*

- [gui-standalone-binary.md](../design/gui-standalone-binary.md) — umbrella for the compiled
  pyobs-gui binary; login pieces done, widget plugin/selection + real plugin smoke test still open.
- [interface_versioning.md](../design/interface_versioning.md) — additive interface versioning
  (`IDome`, `IDomeV2`, ...) (#819). Sanity-checked against `develop` 2026-08-28 (MRO/diamond,
  registration, discovery, wire round-trip all verified); gaps recorded before a plan; no plan yet.

### Sibling repos

One line per plan — same layout for every repo.

- **pyobs-portal** — [2026-09-02-instrument-capability-estimate-duration-endpoint.md](../../pyobs-portal/specs/plans/2026-09-02-instrument-capability-estimate-duration-endpoint.md) —
  this repo's half of pyobs-core's (now-closed) instrument-capability duration estimates: a
  TTL-cached `get_instrument_capabilities()` helper feeding `schema.py`'s `estimate_duration/`,
  plus a `last_instrument_update/` marker for `PortalTaskArchive` to poll (*proposed*, no issue;
  Repos: pyobs-portal, pyobs-core)
- **pyobs-web-client** — [idatasequence](../../pyobs-web-client/specs/plans/2026-08-03-idatasequence.md) —
  `IDataSequence` support ("grab N images") (*proposed*)
- **pyobs-web-client** — [rpc-fault-call-id](../../pyobs-web-client/specs/plans/2026-08-03-rpc-fault-call-id.md) —
  surface `call_id` on RPC faults (*proposed*)
- **pyobs-web-client** — [struct-typed-command-params](../../pyobs-web-client/specs/plans/2026-08-03-struct-typed-command-params.md) —
  `struct<Name>`-typed command params (*blocked on upstream*)
- **pyobs-web-client** — [2026-09-09-safe-area-insets.md](../../pyobs-web-client/specs/plans/2026-09-09-safe-area-insets.md) —
  status bar / gesture-nav inset handling for the compact shell + FAB, split out of
  mobile-first-redesign Phase 3 (*proposed*)
- **pyobs-web-client** — [2026-09-06-mobile-first-redesign.md](../../pyobs-web-client/specs/plans/2026-09-06-mobile-first-redesign.md) —
  mobile-first app shell + per-view redesign, breakpoint-adaptive (*in progress* — Phase 1 done;
  Phase 2 done except `SettingsView`; Phases 3-4 not started)
