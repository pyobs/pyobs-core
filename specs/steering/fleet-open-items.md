# Fleet open items: open issues and plans across the pyobs fleet

Status: standing snapshot — last checked 2026-09-28.

<details>
<summary>Changelog (most recent first)</summary>

- **2026-09-29**: `BaseVideo` redesign opened. Filed pyobs-core #924 (configurable stretch for
  16-bit live-view JPEGs) and #925 (`grab_data()` polling and `_set_image()` sleeps, superseded by
  the grab-path design), pyobs-asi #46 (`AsiVideo`) and pyobs-qhyccd #81 (`QHYCCDVideo`), all
  assigned to Tim. Added four *proposed* design docs (`basevideo-frame-source.md`,
  `basevideo-grab-path.md`, `basevideo-live-view.md`, `guiding-raw-stream.md`) and one plan
  (`2026-09-29-basevideo-frame-buffer-redesign.md`); referenced from pyobs-gui and
  pyobs-web-client `specs/index.md`. Other issue rows not re-checked.
- **2026-09-28**: pyobs-web-client #40-#47 closed on GitHub (all 8 already fixed on `main`, see
  the 2026-09-10 entry for commits) and removed from the issues table, where they had been
  re-added despite that entry. #40 also got a follow-up (`a91be56`, on `develop`): dropped the
  last wire-type label, in `StructConfigForm.vue`. pyobs-web-client has no open issues now.
- **2026-09-28**: Closed out the `IResettable` driver-override follow-up from the entry below.
  Found and fixed a real bug along the way: all 6 GitHub sibling repos (pyobs-aravis, pyobs-asi,
  pyobs-fli, pyobs-flipro, pyobs-qhyccd, pyobs-sbig) had `pyobs-core` locked below v2.11.0 (the
  first release with `IResettable`), so the new `reset()`/`full_reset()` overrides raised
  `AttributeError` at runtime — missed locally (editable install of a newer local `pyobs-core`
  checkout masked it), caught by each repo's own CI resolving its committed lockfile fresh.
  Bumped the `pyobs-core` floor to `>=2.11.0` in all 8 repos (including pyobs-monet/pyobs-iagvt on
  GWDG GitLab) and cut a second patch release everywhere: pyobs-fli v2.0.3, pyobs-flipro v2.0.4,
  pyobs-sbig v2.0.4, pyobs-asi v2.0.4, pyobs-aravis v2.0.4, pyobs-qhyccd v2.0.3, pyobs-monet
  v2.0.7, pyobs-iagvt v2.3.10. All 6 GitHub repos' CI now green. Separately, fixed pyobs-iagvt's
  GitLab CI, which had been failing on every pipeline for 19+ days (unrelated to this plan): its
  CI job token wasn't allowlisted on two transitive git dependencies in the same GitLab group
  (`iagvt/fts-pipe`, `iagvt/opus2py`) — added both via the job-token-scope API, verified pipeline
  861870 now passes ruff/pyrefly/pytest. pyobs-monet still has no `.gitlab-ci.yml` at all (nothing
  to fix there). Closed all 14 upstream issues (12 GitHub + the 2 GitLab work items, #33/#17) with
  comments linking the fixing release, since they'd only been removed from this file's table
  before, not actually closed.
- **2026-09-28**: All 8 `IResettable` driver-override issues from `2026-09-27-data-pipeline-stack-reset.md`
  phase 8 implemented and landed on `develop`: pyobs-aravis (`f855158`), pyobs-asi (`5550ff8`),
  pyobs-fli (`49d8feb`), pyobs-flipro (`98d38cd`), pyobs-qhyccd (`31c5b75`), pyobs-sbig
  (`e73dae3`), plus pyobs-monet (`01b03f3`) and pyobs-iagvt (`1f0587a`) on GWDG GitLab (not
  tracked in the issues table below, which only covers GitHub). Per the maintenance rule, removed
  all 12 GitHub rows (the 6 repos above each had two open issues — a generic "implement the
  overrides" one plus a specific one, both closed out by the same commit) and the plan's "Open
  plans" entry, even though none of the GitHub issues or GitLab work items have actually been
  closed yet. Correction along the way: the pyobs-qhyccd issue's "needs a default policy" framing
  was wrong — `open()` already hardcoded gain=10/offset=140 before reading them back, the phase-7
  survey missed those two lines, so it needed configurable defaults, not a new design decision.
- **2026-09-27**: pyobs-core `2026-09-27-data-pipeline-stack-reset.md` plan landed (`41c82da3`; phases 1-7 for `BaseCamera`/`BaseVideo` + `IResettable`/`IDataPipeline`/`IDataStack` interfaces; released as v2.11.0) — phase 8 (driver issues) waits on Tim's release/go-ahead before merging downstream. Coordinated batch of 14 new driver issues opened on the same day (all 2026-09-27 16:30–17:45 UTC) targeting each camera module to implement the new interface overrides: pyobs-aravis #51/#52, pyobs-asi #42/#43, pyobs-fli #98/#99, pyobs-flipro #48/#49, pyobs-qhyccd #77/#78, pyobs-sbig #86/#87 (each pairing is "implement base override" + "add specialized behavior"). All added to the issues table below. Separate from this: pyobs-core #915 opened 2026-09-23 (`What does BaseTelescope want to know about meridian flips for the first-task logic?`), questioning whether the meridian-flip cutoff logic should move from `OnDemandScheduler` into `BaseTelescope`'s capabilities — waiting on Tim's decision on scope/approach. New: `2026-09-23-pushnotifier-payload-size-cap.md` (implemented 2026-09-23; 12 new tests; addresses MONET/S outage failure modes: cap log-event bodies to FCM's 4 KB limit, skip the notifier's own logs, prune dead tokens, set HTTP timeout). `2026-09-18-pushnotifier-per-user-preferences.md` had status "implemented, uncommitted" but commits now live on `develop` (released in v2.11.0 tag); web-client half also completed, so pyobs-web-client#57 (**closed** 2026-09-27 — both sides done, no web-client preference UI remaining).
- **2026-09-18**: pyobs-core half of pyobs-web-client#57 implemented (plan
  `2026-09-18-pushnotifier-per-user-preferences.md`): `PushNotificationType` enum +
  `IPushNotifications.get_push_preferences`/`set_push_preferences` (and `register_device` renamed
  `register_push_device`), per-account type filtering at send time in `PushNotifier`,
  all-on default with a read-time storage migration; `push-notification-module.md` gains §6 and its
  v1 "one fixed rule set" non-goal is marked superseded. Web-client toggle UI still to do, so #57
  stays in the table.
- **2026-09-18**: re-checked with per-repo `gh issue list` (authoritative — the org-wide
  `search/issues` query the 2026-09-17 check used lagged the same-day #57). #57 is in the table;
  every other open GitHub issue is one whose fix already landed on `develop` (#40-#47,
  pyobs-core#831/#832/#858/#871/#895/#902), so its absence is correct. No plan or design-doc
  changes. The stale status lines corrected alongside the 2026-09-17 entry landed in `5ee33df8`
  (imagewatcher plan + its plans-index entry, and the design index's `irobotic.md`).
- **2026-09-17**: filed pyobs-web-client#57 (let users choose which push notification types they
  receive, per-type opt-in/out for `PushNotifier` (#902) notifications) — added to the issues
  table.
- **2026-09-17**: re-queried the fleet (org-wide `gh api search/issues`): no issue changes since the
  2026-09-15 check — nothing opened, closed, or updated in the window, so the issues table stands
  (pyobs-core#819, pyobs-brot#71, pyobs-gui#168 all still open, none landed on `develop`). Open
  plans and the *proposed* design doc unchanged (`gui-telescopewidget-layout` still partially
  implemented; `interface_versioning` still *proposed*; `mobile-first-redesign` still in progress,
  Phase 4/iOS remaining). New pyobs-core plan `2026-09-17-imagewatcher-retry-hardening.md` (bounded
  exponential backoff + one-time `ERROR` alerting for `ImageWatcher._worker` failures) was written
  and its fix (`061d4f78`) landed on `develop` (and `main`) in the same window — never an open item,
  not added here; its own status line still reads "not yet committed" (stale).
- **2026-09-15**: re-queried the fleet (org-wide `gh api search/issues`). pyobs-core#902
  (`PushNotifier` module) found already **implemented and on `develop`** (`5b688528`, `90b7ded1`,
  committed directly, no PR) — `pyobs.modules.utils.PushNotifier` implementing a new
  `IPushNotifications` interface; the `pyobs-web-client` companion `register_push_device` call also
  landed (`31538b7`). `push-notification-module.md` updated to *implemented* and dropped from the
  open design docs list below. Checked the design doc's three open questions against the shipped
  code: "which interfaces count" was resolved (any state-bearing interface, no allow/deny-list, as
  sketched); stale-token pruning and the exact-message dedup key are **still open as shipped** —
  left as caveats in the design doc rather than split into new issues, pending Tim's call on
  whether either is worth tracking separately. New: pyobs-gui#168 (native desktop notification for
  the same module-`ERROR`/log-`ERROR`-CRITICAL signals, for an operator with pyobs-gui open but not
  watching it — explicitly independent of `PushNotifier`, no design doc yet) — added to the issues
  table. No other org-wide issue changes since the 2026-09-14 check.
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

## Open issues (8, checked 2026-09-28; 4 added 2026-09-29)

One row per issue — same layout for every repo.

| Repo | # | Title | Notes |
|---|---|---|---|
| pyobs-core | [#924](https://github.com/pyobs/pyobs-core/issues/924) | BaseVideo: configurable stretch for 16-bit live view JPEGs | filed 2026-09-29; fixed in PR #926 (not yet merged) |
| pyobs-core | [#925](https://github.com/pyobs/pyobs-core/issues/925) | BaseVideo: replace grab_data() polling and _set_image() sleeps with a future | filed 2026-09-29; fixed by the grab-path redesign in PR #926 (not yet merged) |
| pyobs-core | [#915](https://github.com/pyobs/pyobs-core/issues/915) | Does BaseTelescope want to know about meridian flips? | filed 2026-09-23; design-stage, waiting on Tim's decision on whether meridian-flip cutoff logic should move from `OnDemandScheduler` into `BaseTelescope` capabilities |
| pyobs-core | [#819](https://github.com/pyobs/pyobs-core/issues/819) | Proposal: additive interface versioning (`IDome`, `IDomeV2`, ...) | *design* — design doc landed 2026-08-28 and sanity-checked against `develop`; no plan yet |
| pyobs-brot | [#71](https://github.com/pyobs/pyobs-brot/issues/71) | Investigate root cause of settle timeouts on MONET South (was #61) | *bug* — split from #61 after its mitigation (staleness detection) shipped but was confirmed via the real PLC source not to explain the original symptom; needs mount-side telemetry/drive-fault investigation for the 2026-08-24 incident |
| pyobs-asi | [#46](https://github.com/pyobs/pyobs-asi/issues/46) | Add AsiVideo module implementing IVideo | filed 2026-09-29; to be written on the new `frames()` contract (`basevideo-frame-source.md`), plan phase 3b; no per-frame timestamps in live mode |
| pyobs-qhyccd | [#81](https://github.com/pyobs/pyobs-qhyccd/issues/81) | Add QHYCCDVideo module implementing IVideo | filed 2026-09-29; needs live-mode Cython bindings first; plan phase 3b; no per-frame timestamps in live mode |
| pyobs-gui | [#168](https://github.com/pyobs/pyobs-gui/issues/168) | Desktop notifications for module ERROR / log ERROR-CRITICAL while running | filed 2026-09-14; independent of pyobs-core's push-notification module — same signals, but for an operator already at a running/connected pyobs-gui, via `QSystemTrayIcon::showMessage()` (not decided); no design doc yet |

## Open plans

### pyobs-core `specs/plans/`

- [2026-07-29-gui-telescopewidget-layout.md](../plans/2026-07-29-gui-telescopewidget-layout.md) —
  *partially implemented* (pyobs-gui `2ef4b55`). `TelescopeWidget` width-floor fixes #1
  (`MoveStack`) and #3 (`WrapLongRows`) landed; #4 (breakpoint reflow) likely moot, see below.
- [2026-09-29-basevideo-frame-buffer-redesign.md](../plans/2026-09-29-basevideo-frame-buffer-redesign.md):
  *in progress*. pyobs-core phases (1, 2, 4, 5, server side of 6) in PR #926 (2026-09-29);
  driver migration (3, 3b, 7), clients (6) and shim removal (8) open.

### Design docs still *proposed*

- [basevideo-frame-source.md](../design/basevideo-frame-source.md),
  [basevideo-grab-path.md](../design/basevideo-grab-path.md),
  [basevideo-live-view.md](../design/basevideo-live-view.md),
  [guiding-raw-stream.md](../design/guiding-raw-stream.md): `BaseVideo` redesign (frame buffer and
  driver contract, grab path, selectable live view, stream guiding) (#924, #925). pyobs-core side
  implemented in PR #926, not yet merged; implementation notes at the end of each doc.
- [interface_versioning.md](../design/interface_versioning.md) — additive interface versioning
  (`IDome`, `IDomeV2`, ...) (#819). Sanity-checked against `develop` 2026-08-28 (MRO/diamond,
  registration, discovery, wire round-trip all verified); gaps recorded before a plan; no plan yet.

### Sibling repos

One line per plan — same layout for every repo.

- **pyobs-web-client** — [2026-09-06-mobile-first-redesign.md](../../pyobs-web-client/specs/plans/2026-09-06-mobile-first-redesign.md) —
  mobile-first app shell + per-view redesign, breakpoint-adaptive (*in progress* — Phases 1-3 done
  and real-device verified; only Phase 4, iOS, remains, blocked on Mac access)
