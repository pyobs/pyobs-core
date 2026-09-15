# Fleet open items: open issues and plans across the pyobs fleet

Status: standing snapshot — last checked 2026-09-15.

<details>
<summary>Changelog (most recent first)</summary>

- **2026-09-15**: qfitswidget's responsive toolbar (`2026-09-14-fitswidget-toolbar-overflow.md`,
  hosted in pyobs-gui's specs/) released in qfitswidget v1.1.3; pyobs-gui's floor bumped to match
  and released in v2.4.2 (also picks up today's TelescopeWidget/sidebar/scroll-fallback fixes).
  Live testing after the "implemented" changelog entry below surfaced five *more* real bugs beyond
  the original three — a minimumSizeHint chicken-and-egg deadlock specific to being embedded in a
  resizable QScrollArea, missing hysteresis causing real flicker, a `uv run` auto-sync trap that
  silently discarded a manual editable install across several rounds of "still broken" reports (so
  none of those rounds' fixes were ever actually running), a `QWidgetAction.deleteLater()` crash
  only reproducible with a real Qt event loop pumped, and a one-tier-deep repeat of the
  minimumSizeHint bug for the second overflow-able checkbox. See the plan doc's "Implementation
  notes" for the full account.
- **2026-09-14**: pyobs-gui's `2026-09-14-fitswidget-toolbar-overflow.md` implemented (Repos:
  qfitswidget) — responsive Cuts/Stretch/Colormap toolbar in `QFitsWidget`, hide-then-overflow as
  width shrinks. Design changed mid-implementation from hardcoded pixel thresholds to
  runtime-measured ones (Tim's objection: a hand-picked number drifts with font/DPI/style/text
  changes). Three real bugs found and fixed via headless testing: a dangling `QWidgetAction`
  widget on restore (needed `releaseWidget()`, not plain reparenting), `addWidget()`'s reparent
  silently re-hiding a just-restored widget (`setVisible(True)` must come after, not before), and
  `resizeEvent` reading `self.width()` instead of `event.size().width()`. Dropped from the
  open-plans list.
- **2026-09-14**: two stale pyobs-web-client entries corrected. `idatasequence` was listed
  *proposed*; it's done — count/delay/progress/abort and per-grab image display all
  implemented and live-verified against `pyobs-core` 2.8.9 (the per-grab image display needed
  a separate fix, pyobs-web-client#56: event subscription targeted the wrong pubsub host/node
  id, silently breaking live event delivery fleet-wide in that client — found, fixed, and
  closed same day, so never added to the issues table above). `struct-typed-command-params`
  was listed *in progress — uncommitted working-tree changes*; it landed days ago
  (`a6fbf18`, already on `develop` before this correction). Both dropped from the sibling-repos
  open-plans list.
- **2026-09-14**: pyobs-gui's `2026-09-14-stacked-widget-scroll-fallback.md` implemented —
  `stackedWidget` wrapped in a `QScrollArea` (`stackedWidgetScroll`) as a general fallback once a
  module page can't shrink further. The flagged mouse-wheel-over-spinbox risk was confirmed real
  (headless test: an unfocused spinbox's value changed on a wheel event) and fixed with an
  app-wide event filter (`nowheelfilter.py`). Dropped from the open-plans list.
- **2026-09-14**: pyobs-web-admin#95 (server-side log grep over full history) fixed, released in
  v2.3.4 (`d3014c4`), and closed by another session — missed in this doc until Tim asked about it.
  Dropped from the issues table.
- **2026-09-14**: pyobs-core#859 closed as not worth it — `Scheduler`'s full reschedule on every
  task start/finish means a later-slot task from one `OnDemandScheduler.schedule()` pass never
  executes off that same pass's estimate, so the fudged slew distance this issue would fix
  self-corrects before it matters, except inside `check_for_better_task`/`can_postpone_task`'s
  same-pass lookahead — judged unlikely to flip a real decision (same "no observed operational
  symptom" bar #858 was rejected on). Dropped from the issues table.
- **2026-09-14**: `gui-standalone-binary.md` rejected (Tim: the real build came out several GB, not
  a viable one-file download for a non-technical remote observer) — dropped from both the open
  design docs list and `2026-07-27-gui-widget-plugins-and-packaging.md` from the open plans list
  (that plan's own purpose was serving this goal, now moot). The login-deferral/login-window pair
  underneath it already shipped independently and isn't affected.
- **2026-09-14**: pyobs-core#899 (ACL-denial faults missing `call_id`/proper fault encoding) fixed,
  released in v2.8.9, and closed — per
  `specs/plans/2026-09-14-forbidden-error-call-id-and-fault-encoding.md`. Dropped from the issues
  table.
- **2026-09-14**: pyobs-web-client#54 and pyobs-gui#167 (RPC fault `call_id`) both closed —
  implemented in pyobs-web-client (`86e96c2`, Shell's command log now shows `call_id`) per
  `specs/plans/2026-08-03-rpc-fault-call-id.md`; pyobs-gui's own side of #167 was the same fix
  landing client-side, no separate pyobs-gui change needed. Dropped from the issues table and the
  `rpc-fault-call-id` plan dropped from the sibling-repos open-plans list (done). Live-verifying it
  surfaced a related gap: ACL-denial faults (`ForbiddenError` from `Module.execute()`'s pre-`try`
  ACL check) carry no `call_id` and don't even arrive as a parseable RPC `<fault>` client-side —
  raw XMPP-level error instead. Split out to new pyobs-core#899 (`fed5068` references it from
  pyobs-web-client), added to the issues table below — no plan yet.
  `struct-typed-command-params.md` (unblocked by #898 landing) is now actively being implemented in
  pyobs-web-client — uncommitted working-tree changes there (`pyobs-codec.ts`, `ParamForm.vue`,
  `useXmpp.ts`, `ShellView.vue`, plus a new spec file) build struct-typed params/widgets from the
  `disco#info` field schema; not yet committed, so left as *in progress* rather than done.
- **2026-09-14**: pyobs-brot#61 closed — settle loops across telescope/dome/roof drivers now
  detect a stalled MQTT telemetry stream (`pybrotlib` 1.2.2's new `Transport.telemetry_age()`) and
  fail fast with a distinct `MoveError` instead of silently spinning to the outer `@timeout`;
  offset/focus setpoints also periodically resent as defense-in-depth against MQTT's QoS-0 command
  delivery. Landed `pybrotlib` 1.2.1→1.2.2, `pyobs-brot` 2.0.3→2.0.4, per
  `specs/plans/2026-09-14-brot-settle-loop-staleness-and-resend.md`. **Caveat, checked against the
  real PLC source (`~/code/brotlib`)**: the resend does not explain this issue's actual symptom — a
  dropped offset command would show as instant false convergence, not the sustained elevated
  `TARGETDISTANCE` reported. The genuine drive-fault/following-error root cause is still
  unconfirmed. Split out to pyobs-brot#71 (added to the issues table below) so it stays tracked.
  #61 itself dropped from the issues table.
- **2026-09-14**: pyobs-brot#68 closed — `MQTTTransport.run()` now auto-reconnects with exponential
  backoff (1s-30s) instead of dying silently on disconnect, and resets `_connected`/
  `_connected_event` immediately so `publish()` correctly blocks through an outage instead of
  racing a stale client. Landed `pybrotlib` 1.2.0→1.2.1, `pyobs-brot` 2.0.2→2.0.3, per `pyBROT`'s
  own `specs/plans/mqtt-reconnect.md`. Dropped from the issues table.
- **2026-09-14**: pyobs-core#898 closed — struct field schemas (name/type/unit) now published in
  disco#info's `<types>` block alongside `<enum>`, generalizing existing enum treatment; nesting
  capped at one level (the cap doubles as the cycle guard for self-/mutually-recursive structs).
  Landed on `develop` (`f34184de`), 10 new unit tests. Unblocks pyobs-web-client's
  `struct-typed-command-params.md` plan below. Dropped from the issues table.
- **2026-09-14**: pyobs-core#846 closed — on hold and not required at the moment (caller-level
  archive/site inheritance for `DarkBiasScript`); revisit if the redundancy becomes a real pain
  point. Dropped from the issues table.
- **2026-09-14**: pyobs-core#884 closed — pyobs-web-client is the Android app now (mobile-first
  redesign covers the need), no separate native mobile app needed. Dropped from the issues table.
- **2026-09-14**: re-queried the fleet. New: pyobs-core#898 (publish struct field schemas in
  `disco#info`, like `enum(Name)` does) — this is the upstream blocker pyobs-web-client's
  `struct-typed-command-params.md` plan has been waiting on. pyobs-web-admin#95 (log filtering
  should grep the real log/journal on the server, over all history when no date is set) — opened
  2026-09-12, missed in the last check; pyobs-web-admin re-added to the issues table (had been
  dropped 2026-09-03 when #89 closed and nothing else was open). Dropped pyobs-portal's
  `instrument-capability-estimate-duration-endpoint.md` — its own status line already says
  implemented/closed 2026-09-03, just stale in this doc. Added pyobs-core design doc
  `push-notification-module.md` (sketch stage — direction and v1 scope decided, not yet built;
  written 2026-09-09, missed). pyobs-allsky-cloudcover/pyobs-astrometry/pyobs-dashboard-utils
  confirmed 0 open issues each (no local checkout to check their plans). No other changes.
- **2026-09-13**: pyobs-web-client #49 (reconnect on connection drop) and #48 (auth for embedding
  other pyobs apps) both real-device verified and closed — dropped from the issues table. #49's
  fix (PR #50) turned out to have a real hang bug found during verification (`DISCONNECTED` firing
  without a prior `CONNFAIL` left `attemptReconnect()`'s retry loop stuck on the connecting spinner
  indefinitely — fixed in the same pass, `8808c62`). #48 landed as plain external links (PR #51),
  not the originally-proposed in-app overlay. Also same day: #52 (show connected server in the
  header) and #53 (non-native web build fell back to plaintext password storage, unlike
  pyobs-polaris's `QtKeychain`, which never does — found comparing the two apps' saved-connections
  models) both filed and closed same day, not added to the table. New: pyobs-web-client#54 and
  pyobs-gui#167 (both "surface RPC fault `call_id` for correlating with server-side logs",
  cross-filed same day, both assigned to Tim) — added to the table below, pyobs-gui newly appearing
  there. `mobile-first-redesign.md` now fully done through Phase 2 (`SettingsView` migrated) and
  Phase 3 (`safe-area-insets`/`keyboard-avoidance`, both real-device verified) — only Phase 4 (iOS,
  blocked on Mac access) remains; `safe-area-insets.md` dropped from the open-plans list below
  (done). Also: `testing/pyobs-gui-configs/xmpp/*.yaml`'s stale `name:`→`label:` rename finished
  (5 remaining files) plus an independent `port:`→`http_port:` fix found live-testing a new
  token-protected `IVideo` fixture; new `robotic.yaml` fixture added (no fixture existed before for
  either interface).
- **2026-09-13**: pyobs-pipeline#17 (Keycloak login) implemented, released, and deployed live at
  MONET same day — `pyobs_pipeline.authentication` app + `pyobs-auth` wiring (v2.2.0), plus a
  same-day follow-up fix for a template bug found in prod (multi-line `{# #}` Django comment
  leaking into rendered HTML — v2.2.1). Keycloak client `pipeline` + group `/pyobs-pipeline`
  created centrally; `thusser` assigned. Closed and
  dropped from the issues table. `specs/design/shared-auth-keycloak.md` and
  `shared-authz-keycloak.md` (living docs) updated with a follow-up note + `Repos:` line —
  this is now a fourth cutover of that design, not just three. ADRs 0011/0014 left untouched
  (frozen decision records, not living docs — same reason web-admin's earlier cutover never
  updated ADR 0011's `Repos:` line either). See pyobs-pipeline's own
  `specs/plans/2026-09-13-keycloak-login.md` for the full writeup.
- **2026-09-13**: pyobs-polaris#6 — MIT `LICENSE` added and README given a
  proof-of-concept/retired-status notice, per the reporter's follow-up request; commented on the
  issue with the commit (`8ce297a`). Issue itself had already been closed won't-fix on 2026-09-10
  (thusser: polaris retiring, pyobs-web-client is the maintained client path) but was missed in
  that day's table update — dropped now.
- **2026-09-13**: #896 closed — a consuming site pushed the darkbias-script implementation using
  the DIRECT-scheduled `SCRIPT` mechanism (`darkbias_<binning>` requests via
  `DarkBiasScript(match_science_exptimes=True)`, 3h windows). Evening zeros deliberately left
  unconverted — `match_science_exptimes` defaults to "the night that just ended," which before
  sunset still resolves to the *previous* night, already covered by morning zeros. Dropped from
  the issues table and pyobs-core's own open-plans list (design landed, doc-only).
- **2026-09-13**: #896's open design question answered and split in two: the general mechanism
  (DIRECT-scheduled `SCRIPT` requests dispatching through the already-built `LcoTaskRunner` →
  `LcoScript` → `DarkBiasScript(match_science_exptimes=True)` chain, sidestepping
  `AstroplanScheduler`'s plan-once limitation) is now pyobs-core's own
  `specs/plans/2026-09-13-per-exptime-darks-on-lco-sites.md` (*accepted* — no pyobs-core code
  change needed, the mechanism already ships). The site-specific instantiation is kept in that
  site's own sibling repo, out of pyobs-core, to avoid baking site config/topology into a
  public-repo doc.
- **2026-09-13**: pyobs-core#891 root cause (`_update()` swallowing the API exception, so
  `_loop()`'s 60s outage backoff was dead code) was already fixed in `bfcdc3f4` and released in
  v2.8.7 — closed and dropped from the issues table. The secondary observation in that issue
  (`weather_api.py`'s `_get_response()` retrying 3x with no delay between attempts) was never
  addressed; noted in the closing comment, no follow-up issue opened.
- **2026-09-13**: pyobs-core#895 fix (branch `895-mastermind-reschedule-on-late-skip`) reviewed
  (state-consistency gap in `Mastermind`'s event-send await, unthrottled skip-reschedule loop in
  `Scheduler` — both fixed; `_same_observation`/reschedule-trigger duplication cleaned up;
  alternatives moved to `specs/adrs/0019-task-skip-reschedule-via-fact-event.md`), opened as PR
  #897, merged to `develop` (`45a9bf51`) — dropped from the issues table and from open plans per
  the maintenance rule; issue stays open pending release to `main`.
- **2026-09-10**: added pyobs-core #896 (`question`, design-stage — how #831/#832's per-exptime
  dark masters map onto an LCO portal + `AstroplanScheduler` site; the reduction
  half and archive API additions apply unchanged, but there's no pyobs task to hang
  `match_science_exptimes` on, pyobs-core can't submit LCO request groups, and
  `AstroplanScheduler` plans once rather than reacting, so four candidate directions are left
  open for Tim's call). pyobs-core#895 fix is on branch `895-mastermind-reschedule-on-late-skip`
  (`4087b5f9`), pending PR — kept in the issues table until it lands on `develop`. Added plan
  pyobs-core `2026-09-10-mastermind-reschedule-on-late-skip.md` (*implemented, pending PR*).
  Re-queried all 26 active fleet repos: no other issue/plan changes.
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

## Open issues (2, checked 2026-09-14)

One row per issue — same layout for every repo.

| Repo | # | Title | Notes |
|---|---|---|---|
| pyobs-core | [#819](https://github.com/pyobs/pyobs-core/issues/819) | Proposal: additive interface versioning (`IDome`, `IDomeV2`, ...) | design doc landed 2026-08-28 and sanity-checked against `develop`; no plan yet |
| pyobs-brot | [#71](https://github.com/pyobs/pyobs-brot/issues/71) | Investigate root cause of settle timeouts on MONET South (was #61) | *bug* — split from #61 after its mitigation (staleness detection) shipped but was confirmed via the real PLC source not to explain the original symptom; needs mount-side telemetry/drive-fault investigation for the 2026-08-24 incident |

## Open plans

### pyobs-core `specs/plans/`

- [2026-07-29-gui-telescopewidget-layout.md](../plans/2026-07-29-gui-telescopewidget-layout.md) —
  *partially implemented* (pyobs-gui `2ef4b55`). `TelescopeWidget` width-floor fixes #1
  (`MoveStack`) and #3 (`WrapLongRows`) landed; #4 (breakpoint reflow) likely moot, see below.
### Design docs still *proposed*

- [interface_versioning.md](../design/interface_versioning.md) — additive interface versioning
  (`IDome`, `IDomeV2`, ...) (#819). Sanity-checked against `develop` 2026-08-28 (MRO/diamond,
  registration, discovery, wire round-trip all verified); gaps recorded before a plan; no plan yet.
- [push-notification-module.md](../design/push-notification-module.md) — sketch stage; direction
  and v1 scope decided, not yet built (Repos: pyobs-core, pyobs-web-client). Tracked by #902
  (filed 2026-09-14 after #884 turned out to be closed for an unrelated reason).

### Sibling repos

One line per plan — same layout for every repo.

- **pyobs-web-client** — [2026-09-06-mobile-first-redesign.md](../../pyobs-web-client/specs/plans/2026-09-06-mobile-first-redesign.md) —
  mobile-first app shell + per-view redesign, breakpoint-adaptive (*in progress* — Phases 1-3 done
  and real-device verified; only Phase 4, iOS, remains, blocked on Mac access)
