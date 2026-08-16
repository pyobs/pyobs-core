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

## Not finished

- [2026-07-27-gui-widget-plugins-and-packaging.md](2026-07-27-gui-widget-plugins-and-packaging.md) —
  widget plugin mechanism + `pyside6-deploy` packaging. **draft** (Repos: pyobs-gui)
- [2026-07-29-gui-telescopewidget-layout.md](2026-07-29-gui-telescopewidget-layout.md) —
  `TelescopeWidget` width-floor investigation. **proposed** (Repos: pyobs-gui)
- [2026-08-05-scheduler-archive-prefetch-for-process-isolation.md](2026-08-05-scheduler-archive-prefetch-for-process-isolation.md) —
  split archive prefetch from CPU-bound merit evaluation. **steps 1-3 implemented**
- [2026-08-08-logevent-double-delivery-investigation.md](2026-08-08-logevent-double-delivery-investigation.md) —
  pyobs-gui receives every LogEvent twice. **investigating, open** (Repos: pyobs-core, pyobs-monet)
- [2026-08-09-object-kwarg-validation.md](2026-08-09-object-kwarg-validation.md) — surface
  unrecognized kwargs in `Object.__init__`. **investigated, not started**
- [2026-08-11-basevideo-raw-frame-streaming.md](2026-08-11-basevideo-raw-frame-streaming.md) —
  raw-frame streaming endpoint in `BaseVideo`. **proposed**
- [2026-08-11-camera-driver-gui-split.md](2026-08-11-camera-driver-gui-split.md) — driver/GUI split
  for all camera modules. **proposed** (Repos: qhyccd, fli, tis, asi, aravis, sbig, flipro, v4l)
- [2026-08-11-core-tier-test-baseline-and-dependabot-automerge.md](2026-08-11-core-tier-test-baseline-and-dependabot-automerge.md) —
  baseline tests + grouped Dependabot auto-merge for core-tier repos. **proposed**
- [2026-08-12-shared-auth-keycloak.md](2026-08-12-shared-auth-keycloak.md) — `pyobs-auth` +
  Keycloak integration. **in progress** (Repos: pyobs-archive, pyobs-robotic-backend)
- [2026-08-15-pydantic-extra-validation.md](2026-08-15-pydantic-extra-validation.md) — make the
  pydantic config layer reject unknown keys. **draft**
