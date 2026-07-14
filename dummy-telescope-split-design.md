# Splitting `DummyTelescope`: Design

## Problem

`DummyTelescope` (`pyobs/modules/telescope/dummytelescope.py`) is one monolithic class implementing every
telescope-adjacent interface at once: `IPointingRaDec`, `IPointingAltAz`, `IOffsetsRaDec`, `IFocuser`, `IFilters`,
`IFitsHeaderBefore`, `ITemperatures`, `ITrackingMode`, `ITrackingRate`, `IPointingBody`, `IPointingOrbitalElements`.

That leaves gaps: nothing in `pyobs-core` implements `IOffsetsAltAz`, even though it already has real consumers
(`pyobs/utils/offsets/applyaltazoffsets.py`, `pyobs/modules/pointing/acquisition.py`) — there's no dummy to test
that path against. Same story, worse, for the solar-pointing interfaces `IPointingHGS` and
`IPointingHelioprojective`: zero implementations anywhere in `pyobs-core`, dummy or real. The only real
implementation of `IPointingHGS` today is external, in `pyobs_iagvt.solartelescope.SolarTelescope` (documented in
`docs/source/config_examples/iagvt.rst`), which `pyobs-core`'s test suite has no way to exercise.

`TODO.md` already flagged "Create a `DummySolarTelescope`" as requested-but-unscoped. This doc scopes that,
plus the `IOffsetsAltAz` gap, together — the pointing-interface work (see `tracking-mode-design.md`) already
established `IPointingHGS`/`IPointingHelioprojective` as first-class pointing frames, so it makes sense to give
them real (if dummy) implementations at the same time.

## Decision: three concrete dummies over one shared base

All three implement the same baseline — `IPointingAltAz` + `IPointingRaDec` — since every telescope in this
codebase supports both regardless of which extra interface it's built to exercise. They diverge only in the one
extra interface (or pair) each exists to test:

| Class | Adds (beyond `IPointingAltAz` + `IPointingRaDec`) | Why |
|---|---|---|
| `DummyRaDecTelescope` | `IOffsetsRaDec`, `IPointingBody`, `IPointingOrbitalElements` | today's default guiding-offset path (what `DummyTelescope` already covers) |
| `DummyAltAzTelescope` | `IOffsetsAltAz`, `IPointingBody`, `IPointingOrbitalElements` | `applyaltazoffsets.py`/`acquisition.py` currently have no driver to test against |
| `DummySolarTelescope` | `IPointingHeliocentricPolar` (renamed from `IPointingHGS`, see below) + `IPointingHelioprojective` | mirrors `pyobs_iagvt`'s real `SolarTelescope`; always tracks the sun |

**Confirmed: `DummySolarTelescope` does *not* get `IPointingBody`/`IPointingOrbitalElements`.** It represents a
telescope dedicated to the Sun; `track_body('jupiter')` on it wouldn't be meaningful. `ITrackingMode`/
`ITrackingRate` stay on the shared base for all three, though — every variant needs at least `ITrackingMode`
(sidereal/off, plus solar for the solar dummy), and the RaDec/AltAz variants need `ITrackingRate` for their
arbitrary-body/orbital-element tracking.

**Confirmed: no backward-compatibility alias for `DummyTelescope`.** Existing YAML configs referencing
`class: pyobs.modules.telescope.DummyTelescope` break; this is an accepted breaking change, not kept as a
subclass/alias of `DummyRaDecTelescope`.

Everything interface-agnostic — position simulation (`_move_task`), focus/filter/temperature drift, `init`/
`park`/`stop_motion`, FITS headers, `IFocuser`/`IFilters`/`ITemperatures`/`IFitsHeaderBefore`/
`FitsNamespaceMixin` — moves into a shared base, `_DummyTelescopeBase`, that none of the three
interface-specific concerns live on. This mirrors how `BaseTelescope` itself
already gates `move_radec`/`move_altaz`/`track_body`/`track_orbital_elements` on
`isinstance(self, IPointingXxx)` — a dummy simply not implementing an interface is enough; no new production-code
hooks are needed in `BaseTelescope` for the split itself.

```python
class _DummyTelescopeBase(BaseTelescope, IFocuser, IFilters, IFitsHeaderBefore, ITemperatures,
                          ITrackingMode, ITrackingRate, FitsNamespaceMixin, metaclass=ABCMeta):
    """Shared simulator: position/motion, focus, filters, temperatures, tracking mode/rate.
    No pointing interfaces."""
    ...

class DummyRaDecTelescope(_DummyTelescopeBase, IPointingRaDec, IPointingAltAz,
                           IOffsetsRaDec, IPointingBody, IPointingOrbitalElements, ...):
    ...

class DummyAltAzTelescope(_DummyTelescopeBase, IPointingRaDec, IPointingAltAz,
                           IOffsetsAltAz, IPointingBody, IPointingOrbitalElements, ...):
    ...

class DummySolarTelescope(_DummyTelescopeBase, IPointingRaDec, IPointingAltAz,
                           IPointingHeliocentricPolar, IPointingHelioprojective, ...):
    ...
```

## Rename: `IPointingHGS` → `IPointingHeliocentricPolar`

**Decided, breaking.** `IPointingHGS`'s `lon`/`lat` fields currently represent Heliographic Stonyhurst
coordinates (fixed to the Sun's own rotating surface — e.g. tracking a sunspot) — that's what
`pyobs_iagvt.solartelescope.SolarTelescope` implements it for today, per `iagvt.rst`. Heliocentric Polar
(`mu`/`psi`, disk-projected, unrelated to solar rotation) is a different frame, already used by
`HeliocentricPolarTarget` (`pyobs/robotic/scheduler/targets/heliocentricpolartarget.py`). The interface's own
docstring ("The module can move to Mu/Psi coordinates") was already wrong for what the fields actually encode —
that inconsistency is resolved by fixing the fields to match the name, not the other way round.

This is confirmed as a rename-and-repurpose, not an addition alongside the existing interface: Heliographic
Stonyhurst support is dropped from `pyobs-core` in favor of Heliocentric Polar. `pyobs_iagvt`'s `SolarTelescope`
and `docs/source/config_examples/iagvt.rst` currently claim `IPointingHGS`/HGS support and will need reworking
to match — out of scope for `pyobs-core` itself, but a real, external consequence of this change (tracked
separately, see "Resolved" below).

Renames:

| Before | After |
|---|---|
| `IPointingHGS` (`pyobs/interfaces/IPointingHGS.py`) | `IPointingHeliocentricPolar` (`pyobs/interfaces/IPointingHeliocentricPolar.py`) |
| `HGSState(lon, lat)` | `HeliocentricPolarState(mu, psi)` |
| `move_hgs_lon_lat(lon, lat)` | `move_heliocentric_polar(mu, psi)` |

Conversion mirrors `HeliocentricPolarTarget.coordinates()`: `mu`/`psi` → `sunpy.coordinates.Helioprojective`
(`alpha = arccos(mu)`, `theta` from Sun-Earth distance and solar radius, `tx = -theta·sin(psi)`,
`ty = theta·cos(psi)`) → transform to ICRS for the actual `move_radec` call.

Impact (files referencing the old name, to update once implemented):

- `pyobs/interfaces/IPointingHGS.py` — rename file, class, dataclass, method, fields.
- `pyobs/interfaces/__init__.py` — import and `__all__` entries.
- `docs/source/api/interfaces.rst` — autoclass block.
- `docs/source/whatsnew-2.0.rst` — interface summary table row.
- `docs/source/config_examples/iagvt.rst` — describes `pyobs_iagvt.solartelescope.SolarTelescope` implementing
  `IPointingHGS`; needs rewording once that package is updated (external repo, tracked separately).

## `DummySolarTelescope` always tracks the sun

Confirmed: this dummy's purpose is specifically solar tracking, not a generic "supports more interfaces"
telescope. Per `tracking-mode-design.md`'s already-established principle table (`IPointingHGS`/
`IPointingHelioprojective` → natural tracking behavior "solar" → discrete `TrackingMode.SOLAR`),
`move_heliocentric_polar`/`move_helioprojective` should reset `TrackingMode` to `SOLAR` as a side effect, the
same way `move_radec`/`move_altaz` already reset to `SIDEREAL`/`OFF`. That doc noted this reset was "worth
adding only once a concrete solar-telescope class implements `ITrackingMode` with more than one option" —
`DummySolarTelescope` is that class, since it also carries `IPointingRaDec`/`IPointingAltAz`.

A fixed Heliocentric Polar or Helioprojective coordinate isn't static in RA/Dec — the Sun moves across the sky
and (for a point tied to solar rotation) the Sun itself rotates, so simulating it needs continuous
re-resolution.

### Resolve-and-track logic lives in `DummySolarTelescope` only, not `BaseTelescope`

**Resolved.** The real `pyobs_iagvt.solartelescope.SolarTelescope` tracks the Sun natively in hardware — the
mount's own firmware handles solar tracking once told to, with no RA/Dec ephemeris computation needed on the
pyobs side at all. That removes the original motivation for putting this in `BaseTelescope` (a real driver
"getting it for free"): there's no real driver to share it with. This is purely a simulator concern, so it
belongs entirely in `DummySolarTelescope`.

Shape: a background task on `DummySolarTelescope` (a sibling to `_DummyTelescopeBase._move_task`, not a
modification of it) that, while a Heliocentric Polar/Helioprojective target is active:

1. Recomputes the Sun's current position (`astropy.coordinates.get_sun`/`get_body("sun", ...)`).
2. Reapplies the fixed disk-relative offset established by the last `move_heliocentric_polar`/
   `move_helioprojective` call (the one-shot `mu`/`psi` → `Helioprojective` → ICRS conversion described above,
   giving an RA/Dec target).
3. Updates the simulated position directly (same mechanism `_move_task` already uses to simulate drift/rate
   motion, just Sun-relative instead of a fixed target or computed rate).

No `_tracked_body`/`_resolve_body`-style generic machinery in `BaseTelescope` is needed for this — `IPointingBody`/
`IPointingOrbitalElements` stay exactly as they are today, unrelated to this path (and, per the note above,
`DummySolarTelescope` doesn't implement them anyway).

## Implemented

Fully implemented, one file per class, matching the existing `pyobs/modules/pointing/` convention
(`_base.py`/`_baseguiding.py` as private bases, one file per concrete module):

- `pyobs/modules/telescope/_dummytelescopebase.py` — `_DummyTelescopeBase`
- `pyobs/modules/telescope/dummyradectelescope.py` — `DummyRaDecTelescope`
- `pyobs/modules/telescope/dummyaltaztelescope.py` — `DummyAltAzTelescope`
- `pyobs/modules/telescope/dummysolartelescope.py` — `DummySolarTelescope`

`pyobs/modules/telescope/dummytelescope.py` (the old single-file module) is gone.

## Resolved

- `DummySolarTelescope` does not implement `IPointingBody`/`IPointingOrbitalElements`.
- No backward-compatibility alias for `DummyTelescope` — existing YAML configs referencing it break.
- `pyobs_iagvt`'s `SolarTelescope`/`iagvt.rst` rework is tracked separately, not part of this work.
- Sun-following logic lives entirely in `DummySolarTelescope` (a dedicated background task), not in
  `BaseTelescope` — the real hardware driver tracks the Sun natively, so there's no shared logic to hoist.
