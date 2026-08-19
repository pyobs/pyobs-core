# Plans

Implementation plans, checklist-style. Newest at the bottom.

- [2026-07-19-pyobs_2_0_work_plan.md](2026-07-19-pyobs_2_0_work_plan.md) — pyobs 2.0 rollout.
  **implemented, closed** (Repos: pyobs-core, pyobs-gui)
- [2026-07-19-exception-handling.md](2026-07-19-exception-handling.md) — exception handling across
  the RPC boundary (reconstructed). **implemented, closed**
- [2026-07-19-icamera-iexposure.md](2026-07-19-icamera-iexposure.md) — decouple `ICamera`/
  `IExposure` (reconstructed). **implemented, closed**
- [2026-07-19-idatasequence.md](2026-07-19-idatasequence.md) — `IDataSequence` server-side counted
  sequences (reconstructed). **implemented, closed**
- [2026-07-19-image-trim.md](2026-07-19-image-trim.md) — unify TRIMSEC into `Image.trim()`
  (reconstructed). **implemented, closed**
- [2026-07-19-module-observer-location.md](2026-07-19-module-observer-location.md) — module
  observer-location capabilities (reconstructed). **implemented, closed**
- [2026-07-22-ejabberd-throughput-benchmarking.md](2026-07-22-ejabberd-throughput-benchmarking.md) —
  systematic ejabberd throughput/latency benchmarking. **closed, out of scope** (Repos: pyobs-brot)
- [2026-07-22-enforce-state-publishing.md](2026-07-22-enforce-state-publishing.md) — enforce state
  publishing for stateful interfaces. **implemented, closed** (Repos: pyobs-brot)
- [2026-07-22-state-freshness-max-age.md](2026-07-22-state-freshness-max-age.md) — `max_age` for
  `get_state()`/`wait_for_state()`. **implemented, closed**
- [2026-07-26-gui-interactive-login.md](2026-07-26-gui-interactive-login.md) — interactive
  login/settings dialog for pyobs-gui. **implemented, closed** (Repos: pyobs-core, pyobs-gui)
- [2026-07-27-gui-login-window.md](2026-07-27-gui-login-window.md) — pyobs-gui login window.
  **implemented, closed** (Repos: pyobs-gui, pyobs-core)
- [2026-07-29-gui-acl-aware-widget-gating.md](2026-07-29-gui-acl-aware-widget-gating.md) — ACL-aware
  widget gating. **implemented, closed** (Repos: pyobs-gui, pyobs-core)
- [2026-07-29-gui-iacquisition-widget.md](2026-07-29-gui-iacquisition-widget.md) — `IAcquisition`
  widget. **implemented, closed** (Repos: pyobs-gui, pyobs-core)
- [2026-07-29-gui-iautofocus-widget.md](2026-07-29-gui-iautofocus-widget.md) — `IAutoFocus` widget.
  **implemented, closed** (Repos: pyobs-gui, pyobs-core)
- [2026-07-29-gui-iautoguiding-widget.md](2026-07-29-gui-iautoguiding-widget.md) — `IAutoGuiding`
  widget. **implemented, closed** (Repos: pyobs-gui, pyobs-core)
- [2026-07-29-gui-navbar-shortcuts.md](2026-07-29-gui-navbar-shortcuts.md) — navbar keyboard
  shortcuts. **implemented, closed** (Repos: pyobs-gui)
- [2026-07-31-pipeline-step-error-control.md](2026-07-31-pipeline-step-error-control.md) — per-step
  error control in image-processing pipelines. **implemented**
- [2026-08-03-scheduler-event-loop-blocking.md](2026-08-03-scheduler-event-loop-blocking.md) — stop
  scheduler constraint/merit evaluation blocking the event loop. **implemented**
- [2026-08-04-event-role-advertising.md](2026-08-04-event-role-advertising.md) — advertise event
  send/subscribe role in disco#info. **implemented, closed** (Repos: pyobs-core, pyobs-web-client)
- [2026-08-04-httpfilecache-cors-token-auth.md](2026-08-04-httpfilecache-cors-token-auth.md) — CORS
  + token auth for `HttpFileCache`. **implemented, closed** (Repos: pyobs-core, pyobs-web-client)
- [2026-08-08-pyobs-pipeline.md](2026-08-08-pyobs-pipeline.md) — pyobs-pipeline. **implemented**
  (Repos: pyobs-pipeline)
- [2026-08-09-night-archive-io-hardening.md](2026-08-09-night-archive-io-hardening.md) — rename
  `Night` → `Reduction`, complete `LocalArchive` I/O. **implemented**
- [2026-08-15-log-loaded-pyobs-package-versions.md](2026-08-15-log-loaded-pyobs-package-versions.md) —
  log loaded pyobs-* package versions at module startup. **implemented**
- [2026-08-16-fits-header-fetch-timeout.md](2026-08-16-fits-header-fetch-timeout.md) — bound the
  FITS-header fetch so a dead peer can't stall the frame. **implemented, closed**
- [2026-08-15-pydantic-extra-validation.md](2026-08-15-pydantic-extra-validation.md) — make the
  pydantic config layer reject unknown keys. **implemented, closed** (merged as `e398117f`, #762;
  closed #755)
- [2026-08-05-scheduler-archive-prefetch-for-process-isolation.md](2026-08-05-scheduler-archive-prefetch-for-process-isolation.md) —
  split archive prefetch from CPU-bound merit evaluation. **steps 1-3 implemented 2026-08-06; step
  4 (`ProcessPoolExecutor` swap) dropped 2026-08-15, stress test showed no GIL contention at 6x
  scale — doc recommends marking closed**
- [2026-08-09-object-kwarg-validation.md](2026-08-09-object-kwarg-validation.md) — surface
  unrecognized kwargs in `Object.__init__`. **implemented, closed 2026-08-19** (comm_cfg leak fixed
  at source, #773; fleet cleanup done; enforcement landed as #782, prerequisite was
  2026-08-18-cooperative-mixin-init.md)
- [2026-08-18-cooperative-mixin-init.md](2026-08-18-cooperative-mixin-init.md) — convert mixin
  `__init__` fan-out to cooperative `super()` chains across 10 repos, prerequisite for
  `Object.__init__` raise enforcement. **implemented, closed 2026-08-19**, all 10/10 repos merged,
  `pyobs-core` released as `v2.0.0.dev82` (Repos: pyobs-core, pyobs-alpaca, pyobs-brot, pyobs-fli,
  pyobs-gemini, pyobs-iagvt, pyobs-monet, pyobs-monti, pyobs-sbig, pyobs-zwoeaf)
- [2026-08-16-logevent-double-delivery-fix-discussion.md](2026-08-16-logevent-double-delivery-fix-discussion.md) —
  discussion notes: drop `add_interest()` to fix `ms` double-delivery, plus whether/how to get
  real interest-based event filtering. **closed** (actioned as ADR 0012 below)
- [2026-08-16-explicit-pubsub-event-subscriptions.md](2026-08-16-explicit-pubsub-event-subscriptions.md) —
  real interest-based event delivery via explicit XEP-0060 subscriptions, decoupled from
  presence. **implemented, closed** (merged 2026-08-16, PR #761; 9 integration tests + full 30/30
  XMPP suite passing). Rollout to production sites is a standalone operational step, not part of
  this plan's closure.

## Not finished

- [2026-07-27-gui-widget-plugins-and-packaging.md](2026-07-27-gui-widget-plugins-and-packaging.md) —
  widget plugin mechanism + `pyside6-deploy` packaging. **draft** (Repos: pyobs-gui)
- [2026-07-29-gui-telescopewidget-layout.md](2026-07-29-gui-telescopewidget-layout.md) —
  `TelescopeWidget` width-floor investigation. **proposed** (Repos: pyobs-gui)
- [2026-08-08-logevent-double-delivery-investigation.md](2026-08-08-logevent-double-delivery-investigation.md) —
  pyobs-gui receives every LogEvent twice. **investigating, open** (Repos: pyobs-core, pyobs-monet)
- [2026-08-11-basevideo-raw-frame-streaming.md](2026-08-11-basevideo-raw-frame-streaming.md) —
  raw-frame streaming endpoint in `BaseVideo`. **implemented, closed**
- [2026-08-11-camera-driver-gui-split.md](2026-08-11-camera-driver-gui-split.md) — driver/GUI split
  for all camera modules. **implemented, closed 2026-08-19** — all 8 repos' findings fixed
  (PRs #59/#66 qhyccd, #32 asi, #41 aravis, #71 sbig, #35 flipro, #19 v4l, #83 fli, #13 tis) and
  the missing gui apps built (fli #85, tis #14); real-hardware verification of the two new gui
  apps tracked separately (blocked on hardware access, no cameras available) (Repos: qhyccd, fli,
  tis, asi, aravis, sbig, flipro, v4l)
- [2026-08-11-core-tier-test-baseline-and-dependabot-automerge.md](2026-08-11-core-tier-test-baseline-and-dependabot-automerge.md) —
  baseline tests + grouped Dependabot auto-merge for core-tier repos. **implemented**
- [2026-08-12-shared-auth-keycloak.md](2026-08-12-shared-auth-keycloak.md) — `pyobs-auth` +
  Keycloak integration. **implemented, closed 2026-08-19** — `pyobs-auth` (`2.0.0.dev7`),
  `pyobs-archive` cutover (`2.0.0.dev8`), and `pyobs-robotic-backend` all landed/released; live
  Keycloak login + logout verified; observation-portal brokering (Section 0) tracked separately,
  Keycloak admin/deployment config only (Repos: pyobs-archive, pyobs-robotic-backend)
