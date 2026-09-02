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
- [2026-08-08-logevent-double-delivery-investigation.md](2026-08-08-logevent-double-delivery-investigation.md) —
  pyobs-gui receives every LogEvent twice. **implemented, closed 2026-08-20** — the fix the
  investigation called for (drop `add_interest()`) landed via PR #761 (explicit XEP-0060
  subscriptions); open threads recorded in the doc: why `ms`'s accounts specifically double-
  delivered, and rollout of #761 to production sites (operational) (Repos: pyobs-core,
  pyobs-monet)
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
- [2026-08-20-backend-archive-marker-loss.md](2026-08-20-backend-archive-marker-loss.md) —
  stop gating backend-archive refreshes on the per-process `last_*_update` marker; re-fetch
  every poll and detect changes by content. **implemented, closed 2026-08-20** (PR #790,
  issue #789 closed; portal root cause fixed separately via #84, closing #83;
  Repos: pyobs-core, pyobs-portal)
- [2026-08-21-keycloak-idp-hint-login.md](2026-08-21-keycloak-idp-hint-login.md) — one-click IdP
  login via `kc_idp_hint`: `IDP_HINT` support in pyobs-auth + dual login buttons (hinted IdP vs.
  local Keycloak account) in the services' login pages. **implemented, closed 2026-08-23** — all
  four repos landed and pinned to `pyobs-auth>=2.0.0.dev9`; live browser E2E / SSO short-circuit /
  deployment env vars are operational follow-ups, not part of this plan's closure (Repos:
  pyobs-auth, pyobs-archive, pyobs-portal, pyobs-web-admin)
- [2026-08-20-imagewatcher-event-loop-blocking.md](2026-08-20-imagewatcher-event-loop-blocking.md) —
  stop `ImageWatcher._worker`'s FITS parse and `LocalFile` I/O from blocking the event loop.
  **implemented, closed 2026-08-23** (PR #798; MONET South incident, 2026-08-20)
- [2026-08-24-rename-robotic-backend-to-portal.md](2026-08-24-rename-robotic-backend-to-portal.md) —
  execute ADR 0013: rename `pyobs-robotic-backend` → `pyobs-portal` fleet-wide; in
  pyobs-core, `pyobs.robotic.storage.backend` → `.storage.portal`,
  `Backend*Archive` → `Portal*Archive`. **implemented, closed 2026-08-25** — code merged
  everywhere; pyobs-core `2.0.0.dev97` (contains the rename) published to PyPI; iagvt/monet
  pins bumped to it and pushed (`612d9e4`, `ab02dfc`) (Repos: pyobs-core, pyobs-portal,
  pyobs-auth, pyobs-archive, pyobs-web-admin, pyobs-iagvt, pyobs-monet)

- [2026-08-28-shared-authz-keycloak.md](2026-08-28-shared-authz-keycloak.md) — centralized
  authorization: Keycloak groups/roles become the source of truth; services gate on token claims
  instead of per-service `is_active` activation (design: `specs/design/shared-authz-keycloak.md`,
  ADR `0014`). **implemented, closed 2026-08-31** — verified released across the stack: pyobs-auth,
  pyobs-archive, pyobs-portal, pyobs-web-admin all on v2.1.0; live-verified on MONET/S web-admin
  (Repos: pyobs-auth, pyobs-archive, pyobs-portal, pyobs-web-admin)
- [2026-08-28-precreate-pubsub-nodes.md](2026-08-28-precreate-pubsub-nodes.md) — pre-create pubsub
  event nodes (not state — enforce-state-publishing already narrows that gap) at module startup
  so subscriptions can land before the first publish (XEP-0060 `create_node`); plus the #824 retry
  hardening (`_retry_delay` exponent clamp, stuck-key cleanup in both retry loops). **implemented,
  closed 2026-08-31** (`ea9fe7ef`) — `_retry_delay` now clamps `min(attempt, 60)` before
  exponentiation; on `develop`, not yet in a tagged release (Repos: pyobs-core)
- [2026-08-28-structuredconfig-widget.md](2026-08-28-structuredconfig-widget.md) — generic
  schema-driven `IStructuredConfig` form widget for pyobs-gui, auto-built from `ConfigSchema`.
  **implemented, closed** (pyobs-gui#154; Repos: pyobs-gui, pyobs-core)

## Not finished
- [2026-08-23-iag50-pyobs-core-2x-migration.md](2026-08-23-iag50-pyobs-core-2x-migration.md) —
  pyobs-iag50's `2.0.0.dev2` version bump was premature (still pinned/locked to pyobs-core 1.x);
  real migration work — grid-API rewrite, `self.proxy()` context-manager change, missing-await
  fixes. **in progress** — `1.x` branch cut, `develop` reset to `2.0.0.dev0`, code fixes not yet
  done, three open questions need Tim's input (Repos: pyobs-iag50)
- [2026-07-27-gui-widget-plugins-and-packaging.md](2026-07-27-gui-widget-plugins-and-packaging.md) —
  widget plugin mechanism + `pyside6-deploy` packaging. **draft** (Repos: pyobs-gui)
- [2026-07-29-gui-telescopewidget-layout.md](2026-07-29-gui-telescopewidget-layout.md) —
  `TelescopeWidget` width-floor investigation. **proposed** (Repos: pyobs-gui)
- [2026-08-11-basevideo-raw-frame-streaming.md](2026-08-11-basevideo-raw-frame-streaming.md) —
  raw-frame streaming endpoint in `BaseVideo`. **implemented, closed**
- [2026-08-11-camera-driver-gui-split.md](2026-08-11-camera-driver-gui-split.md) — driver/GUI split
  for all camera modules. **implemented, closed 2026-08-19** — all 8 repos' findings fixed
  (PRs #59/#66 qhyccd, #32 asi, #41 aravis, #71 sbig, #35 flipro, #19 v4l, #83 fli, #13 tis) and
  the missing gui apps built (fli #85, tis #14); real-hardware verification of the two new gui
  apps tracked separately (blocked on hardware access, no cameras available) (Repos: qhyccd, fli,
  tis, asi, aravis, sbig, flipro, v4l)
- [2026-08-11-core-tier-test-baseline-and-dependabot-automerge.md](2026-08-11-core-tier-test-baseline-and-dependabot-automerge.md) —
  baseline tests + grouped Dependabot auto-merge for core-tier repos. **implemented, closed
  2026-08-19** — tests/CI/pyrefly + grouped dependabot + branch protection across 13 repos, and
  the Dependabot auto-merge workflow (validated live on pyobs-alpaca#33). Closes #752
- [2026-08-12-shared-auth-keycloak.md](2026-08-12-shared-auth-keycloak.md) — `pyobs-auth` +
  Keycloak integration. **implemented, closed 2026-08-19** — `pyobs-auth` (`2.0.0.dev7`),
  `pyobs-archive` cutover (`2.0.0.dev8`), and `pyobs-portal` all landed/released; live
  Keycloak login + logout verified; observation-portal brokering (Section 0) tracked separately,
  Keycloak admin/deployment config only (Repos: pyobs-archive, pyobs-portal)
- [2026-08-19-archive-project-access-control.md](2026-08-19-archive-project-access-control.md) —
  show only images the logged-in user has access to, keyed on projects from
  `pyobs-portal`. **superseded, implemented** — see
  `pyobs-archive/specs/plans/2026-08-20-archive-project-access-control.md` for the current design
  (pyobs/pyobs-archive#42) (Repos: pyobs-archive, pyobs-portal, pyobs-core)
- [2026-08-21-basevideo-http-token-auth.md](2026-08-21-basevideo-http-token-auth.md) —
  shared-token auth + browser login page for `BaseVideo`'s HTTP endpoints (design:
  `specs/design/basevideo-http-auth.md`). **implemented, closed** (Repos: pyobs-core, pyobs-gui)
- [2026-08-24-script-field-interface-annotations.md](2026-08-24-script-field-interface-annotations.md) —
  tag `Script` module-name fields (`ImagingScript.camera`, etc.) with required `pyobs.interfaces`
  via `typing.Annotated`, for pyobs-portal's module dropdowns. **implemented, closed**
  (closed #808, PR #809)
- [2026-08-28-observation-portal-keycloak-auth.md](2026-08-28-observation-portal-keycloak-auth.md) —
  attach observation-portal (MONET fork) to OIDC via generic `mozilla-django-oidc` (no pyobs-auth
  dependency, upstream-submittable), config-gated via `OIDC_ENABLED`, additive next to local
  username/password auth; supersedes Section 0 (portal brokered behind Keycloak) of the
  2026-08-12 plan. **proposed, revised 2026-08-31** (Repos: observation-portal)
- [2026-09-01-morning-darks-match-science-exptimes.md](2026-09-01-morning-darks-match-science-exptimes.md) —
  robotic/archive side of dark-exptime matching: expose `EXPTIME` on the archive API, derive a
  night's distinct science exptimes, `DarkBiasScript` takes darks at those exptimes.
  **implemented** (issue #831, landed on `develop` 2026-09-01 via PR #840; reduction side is
  `2026-09-01-per-exptime-dark-masters.md`)
- [2026-09-01-per-exptime-dark-masters.md](2026-09-01-per-exptime-dark-masters.md) —
  reduction/pipeline side: per-exposure-time dark masters, strict exptime matching, reference
  master scales down only (ADR `0015`). **implemented** (issue #832, landed on `develop`
  2026-09-01 via PR #842; depends on `2026-09-01-morning-darks-match-science-exptimes.md`)
- [2026-09-02-polymorphic-model-dump-exclude-include.md](2026-09-02-polymorphic-model-dump-exclude-include.md) —
  `PolymorphicBaseModel`'s hand-rolled `model_serializer` silently ignores `exclude`/`include`/
  `by_alias`/`exclude_none`/`exclude_defaults`/`exclude_unset`; make it honor flat (non-nested)
  specs and raise `NotImplementedError` on anything nested rather than silently doing the wrong
  thing. **implemented, closed 2026-09-02** (issue #855; PR #857, merged `4baeb68e`; Repos:
  pyobs-core)
- [2026-09-01-instrument-capability-duration-estimates.md](2026-09-01-instrument-capability-duration-estimates.md) —
  feed pyobs-portal#133's instrument capability data (readout/filter-change/slew/dome-rotate
  times) into `Script.estimate_duration()` for `ImagingScript` and 4 other leaf scripts, via a new
  `TaskData.instrument_capabilities` field; wires the portal's script builder and
  `OnDemandScheduler` (not `AstroplanScheduler` — see plan's Non-goals). pyobs-portal-side
  implementation detail (cache helper, `last_instrument_update/` marker, `schema.py` wiring) is
  its own plan: `../../../pyobs-portal/specs/plans/2026-09-02-instrument-capability-estimate-duration-endpoint.md`.
  **proposed** (no issue yet; Repos: pyobs-core, pyobs-portal)
- [2026-09-01-scheduler-reschedule-on-portal-task-removal.md](2026-09-01-scheduler-reschedule-on-portal-task-removal.md) —
  drop `Scheduler._update_schedule()`'s "was it scheduled?" gate, which is unconditionally wrong
  for `PortalObservationArchive` (permanently empty cache by construction) and stalls
  rescheduling when a portal task is deactivated/deleted; plus mastermind self-heals an
  unresolvable *pending* observation by marking it canceled instead of looping forever (review on
  PR #852 caught and fixed a non-nullable-FK payload bug, a startup-race false-cancel, and scoped
  the self-heal off `get_current_observation()`). **implemented** (issue #847; PR #852; Repos:
  pyobs-core)
- [2026-09-01-scheduler-reschedule-on-project-and-task-changes.md](2026-09-01-scheduler-reschedule-on-project-and-task-changes.md) —
  `Scheduler._update_schedule()`'s change-detection is task-ID-only, so a project priority change
  or a same-ID task content change never triggers a reschedule; adds project/task content-diff
  (`model_dump()`-keyed, mirroring `PortalTaskArchive._update()`) plus a fix for an
  assignment-order bug that overwrites `self._projects` before it could ever be compared. Also
  dropped the schedule-membership guard for the new `changed` set, rebasing onto #852's removal
  of that same guard for `removed` (both silently discarded real changes against
  `PortalObservationArchive`'s permanently-empty schedule cache). **implemented** (issue #848; PR
  #854; Repos: pyobs-core; portal-side signal fix pyobs-portal#134)
