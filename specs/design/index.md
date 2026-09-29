# Design docs

Living architecture/design docs, one per feature or subsystem. Kept around after landing
(`status: implemented`), not deleted.

- [basevideo-frame-source.md](basevideo-frame-source.md): base-owned capture loop, timestamped
  frames, settings generation and frame buffer for `BaseVideo`; new `frames()` driver contract.
  *implemented (PR #926), driver migration open* (2026-09-29; Repos: pyobs-core, driver plugins)
- [basevideo-grab-path.md](basevideo-grab-path.md): `grab_data()`/`grab_stack()` as frame-buffer
  consumers, off the frame loop, with exposure-start timing. *implemented (PR #926)* (2026-09-29;
  supersedes the fix in #925; Repos: pyobs-core, driver plugins)
- [basevideo-http-auth.md](basevideo-http-auth.md) — shared-token auth + browser login
  page for `BaseVideo`'s HTTP endpoints. *implemented* (Repos: pyobs-core, pyobs-gui)
- [basevideo-live-view.md](basevideo-live-view.md): user-selectable live view, MJPEG with
  server-side stretch for slow links, raw with client-side stretch/cuts for fast ones; raw-stream
  crop/metadata extensions. *server side implemented (PR #926), clients open* (2026-09-29; #924; Repos: pyobs-core, pyobs-gui,
  pyobs-web-client)
- [basevideo-raw-frame-streaming.md](basevideo-raw-frame-streaming.md) — `BaseVideo` raw-frame
  streaming endpoint alongside the existing MJPEG live view. *implemented*
- [combinestack.md](combinestack.md) — `pyobs.images.processors.stack`: processors that collapse
  an `IDataStack` cube into one frame, one class per method (mean, median, sum, sigma-clip). *implemented*
  (2026-09-27)
- [exception_handling.md](exception_handling.md) — exception handling across the RPC boundary.
  *implemented*
- [external_interfaces_registry.md](external_interfaces_registry.md) — external interfaces
  registry. *implemented, closed*
- [gui-standalone-binary.md](gui-standalone-binary.md) — `pyobs-gui` as a standalone binary.
  *rejected 2026-09-14* — real build came out several GB (Repos: pyobs-core, pyobs-gui)
- [guiding-raw-stream.md](guiding-raw-stream.md): `AutoGuiding` consuming `/video.raw` instead of
  `grab_data()`, discarding frames exposed during corrections. *implemented (PR #926), untested on
  hardware* (2026-09-29)
- [icamera_iexposure.md](icamera_iexposure.md) — decouple camera identity from exposure-progress
  state. *implemented, closed* (#437)
- [idatasequence.md](idatasequence.md) — server-side counted data sequences. *implemented,
  closed* (#548)
- [idatapipeline.md](idatapipeline.md): `IDataPipeline`: named, YAML-configured pipelines
  selected via `set_pipeline()`, result replaces raw data. *implemented* (2026-09-27; Repos:
  pyobs-core, driver plugins)
- [idatastack.md](idatastack.md): `IDataStack`: grab N consecutive frames into one 3D cube,
  combined via the selected pipeline. *implemented* (2026-09-27; Repos: pyobs-core, driver
  plugins)
- [image_trim.md](image_trim.md) — unify the three TRIMSEC implementations into `Image.trim()`.
  *implemented, closed* (#342)
- [irobotic.md](irobotic.md) — `IRobotic` (executor) / `IRoboticScheduler` (planner) interfaces
  and GUI widgets for robotic modules. *implemented, closed* (#825; Repos: pyobs-core,
  pyobs-gui)
- [istructuredconfig.md](istructuredconfig.md) — `IStructuredConfig` bulk structured config.
  *implemented* (pyobs-core `IStructuredConfig.py` + `config_schema.py`, 2026-07-10; consumer:
  pyobs-iagvt's FTS module — see doc status for the pydantic/consumer evolutions)
- [iresettable.md](iresettable.md): `IResettable`: reset a device to its defaults, called at
  startup and by robotic scripts. *implemented* (2026-09-27; Repos: pyobs-core, driver plugins)
- [interface_versioning.md](interface_versioning.md) — additive interface versioning
  (`IDome`, `IDomeV2`, ...). *proposed* (#819; sanity-checked against `develop`, not yet
  implemented; Repos: pyobs-core, pyobs-gui, driver plugins)
- [mobile-app-and-shared-ts-client-core.md](mobile-app-and-shared-ts-client-core.md) — mobile
  client (Android/iOS + tablets) and the shared TypeScript client core for `pyobs-web-client`
  and the app. *superseded 2026-09-06* — replaced by a Capacitor wrapper around
  `pyobs-web-client` itself; see `pyobs-web-client/specs/design/native-app-shell-capacitor.md`
  (issue #884; ADRs 0016–0018, all superseded; Repos: pyobs-core, pyobs-web-client)
- [module_observer_location.md](module_observer_location.md) — module observer-location
  capabilities. *implemented, closed*
- [obsnum_fits_header.md](obsnum_fits_header.md) — `OBSNUM` per-night observation counter in FITS
  headers. *implemented, closed* (#738; Repos: pyobs-core, pyobs-portal)
- [package_versions_fits_header.md](package_versions_fits_header.md) — record loaded pyobs-*
  package versions per module as `HIERARCH <MODULE> VERSION <PACKAGE>` FITS headers. *implemented,
  closed* (#739; `b197528c`)
- [push-notification-module.md](push-notification-module.md) — `PushNotifier` module relaying
  module-`ERROR` state and `ERROR`/`CRITICAL` log events to FCM/APNs, plus per-user
  notification-type preferences (§6). *implemented* (issue #902, previously #884 which closed for
  an unrelated reason; pyobs-web-client#57 for the §6 additions; Repos: pyobs-core,
  pyobs-web-client)
- [pyobs_2_0_wire_protocol.md](pyobs_2_0_wire_protocol.md) — pyobs 2.0 wire protocol, state, and
  access control. *implemented, closed*
- [rpc_gating_on_startup.md](rpc_gating_on_startup.md) — gating RPC commands until module startup
  completes. *implemented, closed* (#673)
- [shared-auth-keycloak.md](shared-auth-keycloak.md) — shared auth across pyobs web projects via
  Keycloak. *implemented* (plan `2026-08-12-shared-auth-keycloak.md` closed 2026-08-19;
  Repos: pyobs-archive, pyobs-portal)
- [shared-authz-keycloak.md](shared-authz-keycloak.md) — centralized authorization via Keycloak
  groups/roles; replaces per-service local activation with token-claim gates. *proposed*
  (issue #823; ADR `0014`; plan `2026-08-28-shared-authz-keycloak.md`;
  Repos: pyobs-auth, pyobs-archive, pyobs-portal, pyobs-web-admin)
