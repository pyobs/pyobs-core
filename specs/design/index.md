# Design docs

Living architecture/design docs, one per feature or subsystem. Kept around after landing
(`status: implemented`), not deleted.

- [basevideo-raw-frame-streaming.md](basevideo-raw-frame-streaming.md) — `BaseVideo` raw-frame
  streaming endpoint alongside the existing MJPEG live view. *implemented*
- [exception_handling.md](exception_handling.md) — exception handling across the RPC boundary.
  *implemented*
- [external_interfaces_registry.md](external_interfaces_registry.md) — external interfaces
  registry. *implemented, closed*
- [gui-standalone-binary.md](gui-standalone-binary.md) — `pyobs-gui` as a standalone binary.
  *proposed* (Repos: pyobs-core, pyobs-gui)
- [icamera_iexposure.md](icamera_iexposure.md) — decouple camera identity from exposure-progress
  state. *implemented, closed* (#437)
- [idatasequence.md](idatasequence.md) — server-side counted data sequences. *implemented,
  closed* (#548)
- [image_trim.md](image_trim.md) — unify the three TRIMSEC implementations into `Image.trim()`.
  *implemented, closed* (#342)
- [istructuredconfig.md](istructuredconfig.md) — `IStructuredConfig` bulk structured config.
  *proposed* (consumer: pyobs-iagvt)
- [module_observer_location.md](module_observer_location.md) — module observer-location
  capabilities. *implemented, closed*
- [obsnum_fits_header.md](obsnum_fits_header.md) — `OBSNUM` per-night observation counter in FITS
  headers. *implemented, closed* (#738; Repos: pyobs-core, pyobs-robotic-backend)
- [pyobs_2_0_wire_protocol.md](pyobs_2_0_wire_protocol.md) — pyobs 2.0 wire protocol, state, and
  access control. *implemented, closed*
- [rpc_gating_on_startup.md](rpc_gating_on_startup.md) — gating RPC commands until module startup
  completes. *implemented, closed* (#673)
- [shared-auth-keycloak.md](shared-auth-keycloak.md) — shared auth across pyobs web projects via
  Keycloak. *proposed* (Repos: pyobs-archive, pyobs-robotic-backend)
