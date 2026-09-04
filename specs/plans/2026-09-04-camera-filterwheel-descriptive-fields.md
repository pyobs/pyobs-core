# Plan: Camera/filter-wheel descriptive fields, required module_name, forward-compatible parsing

Status: implemented, pending PR merge (Repos: pyobs-core, pyobs-portal)

Surfaced while filling in MONET-South's real capability data (`monet/pyobs-monet#3`) through the
portal admin: no field existed to record which physical camera/sensor/filter-wheel model is
actually installed, `FilterWheelCapability.module_name` turned out to be a real bug (see below),
and adding the two new fields immediately broke a running `mastermind` on an older pyobs-core
release, surfacing a design gap the original 2026-09-01 plan had flagged but left undecided.

## 1. Descriptive fields

`CameraCapability` gains `model` (e.g. "FLI ProLine PL23042") and `sensor_type` (e.g. "e2v
CCD230-42, back-illuminated CCD"); `FilterWheelCapability` gains `model` (e.g. "FLI CFW-2-7").
Both blank-ok strings, no behavioral effect — pure reference data, mirrored 1:1 between
pyobs-portal's Django models and pyobs-core's pydantic models.

## 2. FilterWheelCapability.module_name: nullable → required

`module_name` was nullable, documented as "for a wheel with no addressable module of its own (e.g.
integrated into the camera)". In practice this was a bug, not a feature: pyobs-core's
`InstrumentCapabilities.__init__` only indexes filter wheels with a non-`None` module_name
(`if wheel.module_name is not None: self._filter_wheels[...] = wheel`), so a null-module_name row
was **silently unreachable** by any script or scheduler lookup — dead data. The "integrated into
the camera" case this was meant to cover (e.g. `pyobs_sbig.SbigFilterCamera` exposing filter
control through the camera's own module, per `filter_wheel: AUTO` in its config) is correctly
handled by entering the *camera's* module_name on the `FilterWheelCapability` row, not leaving it
blank — there was no real case left for null.

Changed to required on both sides (`str`, no default) — matches `CameraCapability`/
`TelescopeCapability`/`DomeCapability`/`RoofCapability`'s own `module_name` exactly. No existing
production data had a null value (confirmed before making the schema change), so this is a plain
migration, no backfill needed.

## 3. Forward-compatible parsing (`extra="ignore"` for the capability models)

Landed the two field additions above straight into pyobs-portal, and a running `mastermind` on an
still-current-at-the-time pyobs-core release started logging parse failures polling
`/api/instruments/` — because every model in `pyobs/robotic/instruments.py` inherits
`pyobs.utils.serialization.BaseModel`'s `extra="forbid"`, an unrecognized field anywhere in the
payload fails the *entire* response's validation, not just that field. `PortalTaskArchive`
already catches this and degrades to the last-good cache (`_poll_instrument_capabilities`'s broad
`except Exception`), so nothing crashed, but it turned an ordinary field addition into a logged
error and a stale cache until the site's own pyobs-core got upgraded — exactly the risk flagged,
but left undecided, in the original 2026-09-01 plan's design notes ("extra='forbid' on the
§A.1 models degrade-to-None conflict").

Fixed at the source: every model in `pyobs/robotic/instruments.py` now inherits a new
`_ForwardCompatibleModel` base (`BaseModel` subclass, `model_config = ConfigDict(extra="ignore")`)
instead of `BaseModel` directly. `extra="forbid"` stays the right default everywhere else in pyobs
(catching config typos, `2026-08-15-pydantic-extra-validation.md`) — scoped narrowly here because
this module only ever consumes portal-controlled data, and the portal and any given fleet site's
pyobs-core version are never guaranteed to be on the same release. A portal response with a field
an older client doesn't recognize now parses successfully (that field dropped, everything else
intact) instead of rejecting the whole response.

## Test plan

- [x] pyobs-portal: `model`/`sensor_type` round-trip in serializer shape test; `module_name`
      global-uniqueness test rewritten for the now-required field (was "None is fine, multiple
      allowed" — no longer a valid case) — `pyobs_portal/instruments/tests.py`, 25 tests in the
      app, 152 in the full suite.
- [x] pyobs-core: `model`/`sensor_type`/wheel-`model` round-trip; `FilterWheelCapability` with
      `module_name=None` now raises `ValidationError` (was silently unreachable, now a hard
      failure at parse time instead of silent data loss); a payload with unrecognized fields
      mixed in with recognized ones now parses successfully and updates the cache (rewrote
      `test_instrument_capabilities_poll_keeps_last_good_on_unparseable_payload`, which tested
      the old `extra="forbid"` behavior directly, into
      `test_instrument_capabilities_poll_tolerates_unrecognized_fields`) —
      `tests/robotic/test_instruments.py`, `tests/robotic/storage/portal/test_portal_archives.py`,
      504 tests in the full `tests/robotic/` suite.
