# Plan: Plain-roof open/close-time capability field

Status: implemented, pending PR merge (Repos: pyobs-core, pyobs-portal)

Split out of `2026-09-04-first-task-slew-rotate-distance.md` (pyobs-core#858's review discussion,
2026-09-04) as pyobs-core#877: telescope slew time and rotating-dome rotate time both already had
portal-side rate data to consume (`TelescopeCapability.slew_rate_deg_per_s`,
`DomeCapability.rotate_rate_deg_per_s`); a plain open/close roof (`IRoof`, no `IPointingAltAz` --
nothing to rotate toward a target) has no rate/distance concept at all, just a fixed cycle time,
and no field for it existed anywhere -- neither pyobs-core's `instruments.py` nor pyobs-portal's
`instruments` app. That's a portal-side model change first, bigger scope than #858's pure
data-wiring, hence the split (closer in shape to the #139/#140/#142 model-field additions the
original 2026-09-01 plan needed).

**Real motivating need**: MONET-N/MONET-S/MONTI are all plain roofs, no rotating dome
(`monet/pyobs-monet#3`), so this -- not #858's dome piece -- is what actually unblocks accurate
first-task duration estimates for that fleet once the portal admin is filled in.

## Design

### pyobs-portal (`pyobs_portal/instruments/`)

New `RoofCapability` model, parallel to `DomeCapability`: `module_name` (unique),
`open_close_time_s` (nullable float), `OneToOneField(Instrument, related_name="roof")`,
`updated_at`. Wired into:
- `InstrumentSerializer` (new `roof` field) and `RoofCapabilitySerializer`.
- `InstrumentAdmin` (`RoofCapabilityInline`, `StackedInline` like `DomeCapabilityInline`).
- `INSTRUMENT_QUERYSET`'s `select_related` (no N+1 -- a JOIN, not an added query).
- `last_instrument_update/`'s marker `Max()` (now eight models, not seven).
- `instrument-config` group permissions, via a new data migration (0007) rather than editing the
  already-applied 0002 migration -- add/change/delete on `roofcapability`, same shape as every
  other capability model there.

### pyobs-core (`pyobs/robotic/instruments.py` + the three scripts)

`RoofCapability` pydantic model mirrors the portal shape. Unlike `TelescopeCapability`/
`DomeCapability`, **no `estimate_*()` method** -- `open_close_time_s` is already a duration, not a
rate to combine with a distance, so callers use it directly (same pattern as
`FilterWheelCapability.filter_change_time_s`). `InstrumentCapabilities.roof(module_name)` lookup
and `Instrument.roof` field mirror `dome`.

`PointingScript`/`ImagingScript`/`AutoFocusScript` each gain a `roof: str | None` field
(`Annotated[str | None, IRoof]`, default `None`), alongside the existing `telescope`/`dome`
fields. `estimate_duration()` extends the existing `max(slew_time, rotate_time)` to a third
candidate, `roof.open_close_time_s` when present -- telescope and dome/roof move in parallel, so
time-to-ready is the slowest of the three, not their sum. A site has a dome or a roof, never both
in practice, but nothing here enforces that; both fields can be set independently, same as
telescope/dome already are.

## Non-goals

- **Live telescope/dome/roof position** -- out of scope here for the same reason it was dropped
  from #858 (see that plan's History section): no observed accuracy problem justified it.
- **Enforcing "dome xor roof" at the type level** -- not worth the validation complexity for a
  constraint that's a real-world fact about hardware, not a data-integrity risk this app needs to
  guard against (same reasoning as the portal model docstring's `module_name` uniqueness caveat).

## Test plan

- [x] pyobs-portal: `RoofCapability` cascade-delete, serializer round-trip (`roof: null` when
      absent, populated when present), `INSTRUMENT_QUERYSET` N+1 guard now covers roof,
      `last_instrument_update/` moves on a roof-only edit, `instrument-config` group permissions
      include `roofcapability`, migration-idempotency guard for the 0007 data migration —
      `pyobs_portal/instruments/tests.py`, 25 tests in the app, 152 in the full suite.
- [x] pyobs-core: `RoofCapability` model (`open_close_time_s` used directly, no rate/distance
      method), `InstrumentCapabilities.roof()` lookup, `Instrument.roof` round-trips a plain-roof
      site (no dome) — `tests/robotic/test_instruments.py`.
- [x] pyobs-core: `PointingScript`/`ImagingScript`/`AutoFocusScript.estimate_duration()` — roof
      slower than telescope, telescope slower than roof, roof not configured (unaffected) — one
      test per case per script.
