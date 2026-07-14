# Non-Sidereal Tracking: Implementation Plan

## Overview

Four new interfaces (`ITrackingMode`, `ITrackingRate`, `IPointingBody`, `IPointingOrbitalElements`), modifications to `BaseTelescope` and `DummyTelescope`, two new `Unit` members, and a background task for continuous rate/position refresh. No new third-party dependency — orbital-element propagation is hand-rolled on top of `numpy`/`astropy.coordinates` (Phase 5.4).

---

## Phase 1: Foundation

### 1.1 `pyobs/utils/enums.py` — Add new `Unit` members

Add to `Unit` enum:

```python
ARCSEC_PER_SEC = "arcsec/s"
AU = "au"
```

Add to `_ASTROPY_UNITS` mapping:

```python
Unit.ARCSEC_PER_SEC: astropy.units.arcsec / astropy.units.s,
Unit.AU: astropy.units.AU,
```

---

## Phase 2: New Interface Files

All four follow the existing `IPointing*` pattern: `from __future__ import annotations`, `ABCMeta`, `__module__ = "pyobs.interfaces"`, state/capabilities dataclasses with `time: Time = field(default_factory=Time.now)` as last field, `__all__` export list.

### 2.1 `pyobs/interfaces/ITrackingMode.py`

- `TrackingMode(StrEnum)`: `SIDEREAL`, `SOLAR`, `LUNAR`, `OFF`
- `TrackingModeState` dataclass: `mode: TrackingMode`, `time: Time`
- `TrackingModeCapabilities` dataclass: `modes: list[TrackingMode]`
- `ITrackingMode(Interface)`: `state = TrackingModeState`, `capabilities = TrackingModeCapabilities`, abstract `set_tracking_mode(mode: TrackingMode, **kwargs: Any) -> None`

### 2.2 `pyobs/interfaces/ITrackingRate.py`

- `TrackingRateState` dataclass: `ra_rate: Annotated[float, Unit.ARCSEC_PER_SEC]`, `dec_rate: Annotated[float, Unit.ARCSEC_PER_SEC]`, `time: Time`
- `TrackingRateCapabilities` dataclass: `min_update_interval: Annotated[float, Unit.SECONDS]`
- `ITrackingRate(Interface)`: `state = TrackingRateState`, `capabilities = TrackingRateCapabilities`, abstract `set_tracking_rate(ra_rate, dec_rate, **kwargs: Any) -> None`

### 2.3 `pyobs/interfaces/IPointingBody.py`

- No state/capabilities (marker + method interface)
- `IPointingBody(Interface)`: abstract `track_body(body: str, **kwargs: Any) -> None`

### 2.4 `pyobs/interfaces/IPointingOrbitalElements.py`

- `OrbitalElements` dataclass: `epoch: Time`, `semi_major_axis: Annotated[float, Unit.AU]`, `eccentricity: float`, `inclination: Annotated[float, Unit.DEGREES]`, `longitude_ascending_node: Annotated[float, Unit.DEGREES]`, `argument_of_periapsis: Annotated[float, Unit.DEGREES]`, `mean_anomaly: Annotated[float, Unit.DEGREES] | None = None`, `perihelion_time: Time | None = None`
- `IPointingOrbitalElements(Interface)`: abstract `track_orbital_elements(elements: OrbitalElements, **kwargs: Any) -> None`

---

## Phase 3: Wire Up Exports

### 3.1 `pyobs/interfaces/__init__.py`

Add imports:

```python
from .ITrackingMode import ITrackingMode, TrackingMode, TrackingModeState, TrackingModeCapabilities
from .ITrackingRate import ITrackingRate, TrackingRateState, TrackingRateCapabilities
from .IPointingBody import IPointingBody
from .IPointingOrbitalElements import IPointingOrbitalElements, OrbitalElements
```

Add all to `__all__`.

---

## Phase 4: BaseTelescope Modifications

File: `pyobs/modules/telescope/basetelescope.py`

### 4.1 `move_radec` tracking-mode reset (after acquiring lock, before `_move_radec`)

```python
if isinstance(self, ITrackingMode):
    await self.set_tracking_mode(TrackingMode.SIDEREAL)
```

### 4.2 `move_altaz` tracking-mode reset (after acquiring lock, before `_move_altaz`)

```python
if isinstance(self, ITrackingMode):
    await self.set_tracking_mode(TrackingMode.OFF)
```

### 4.3 Add `_set_tracking_rate` abstract method

```python
@abstractmethod
async def _set_tracking_rate(self, ra_rate: float, dec_rate: float) -> None:
    """Actually applies the rate to hardware. Implemented by concrete driver classes."""
    ...
```

### 4.4 Add public `set_tracking_rate` with SIDEREAL precondition

```python
async def set_tracking_rate(self, ra_rate: float, dec_rate: float, **kwargs: Any) -> None:
    """Public entry point. Enforces the SIDEREAL precondition."""
    if isinstance(self, ITrackingMode):
        current = self.comm.get_own_state(ITrackingMode)
        if current is None or current.mode != TrackingMode.SIDEREAL:
            await self.set_tracking_mode(TrackingMode.SIDEREAL)
    await self._set_tracking_rate(ra_rate, dec_rate)
    await self.comm.set_state(ITrackingRate, TrackingRateState(ra_rate=ra_rate, dec_rate=dec_rate))
```

Note: uses `self.comm.get_own_state(ITrackingMode)` — correct API, not the spec's `self.get_state()` which returns `None`.

---

## Phase 5: track_body / track_orbital_elements Implementation

### 5.1 Body name resolution in `BaseTelescope`

```python
async def _resolve_body(self, body: str) -> tuple[float, float]:
    """Resolve a body name to (RA, Dec) in degrees.

    Resolution chain:
    1. astropy.coordinates.get_body — Sun, Moon, major planets
    2. JPL Horizons fallback — anything not covered above
    """
```

- Step 1: `astropy.coordinates.get_body(body, Time.now(), observer=...)` -> SkyCoord -> (ra, dec)
- Step 2: `astroquery.jplhorizons` Horizons class — query by name, get RA/Dec

No automatic MPC/NEOCP-by-designation step. Considered and dropped — see design doc's "Elements source" section: MPC has no formal REST API, so it'd mean scraping an unversioned page, riskiest for exactly the newly-posted-NEOCP-object case this feature is meant to help with. A caller with fresh elements in hand calls `track_orbital_elements(elements)` directly instead — no lookup needed, no scraper to break.

### 5.2 `track_body` implementation

```python
async def track_body(self, body: str, **kwargs: Any) -> None:
    """Slews to body and starts tracking."""
    ra, dec = await self._resolve_body(body)
    await self.move_radec(ra, dec)
    self._start_body_tracking(body)
```

### 5.3 `track_orbital_elements` implementation

```python
async def track_orbital_elements(self, elements: OrbitalElements, **kwargs: Any) -> None:
    """Slews to element-defined body and starts tracking."""
    ra, dec = self._propagate_elements(elements, Time.now())
    await self.move_radec(ra, dec)
    self._start_elements_tracking(elements)
```

### 5.4 Local propagation helper

Hand-rolled two-body Kepler propagation — no orbital-mechanics dependency. `poliastro` (the obvious library) can't actually be installed here: its latest release requires `python>=3.8,<3.11` and `astropy>=5.0,<6`, both incompatible with this project's `python>=3.11`/`astropy>=7.0.1,<9`. Its maintained fork `hapsira` would resolve but pulls in `matplotlib`/`numba`/`plotly` for no benefit over rolling it directly with `numpy` + `astropy.coordinates` (both already core deps). See design doc's "Asteroids/comets" section for the derivation.

```python
def _propagate_elements(elements: OrbitalElements, t: Time) -> tuple[float, float]:
    """Two-body Kepler propagation -> (ra, dec) in degrees."""
    # elliptical: solve M = E - e*sin(E) via Newton-Raphson for E, then
    # true anomaly/heliocentric distance from E, perifocal position,
    # rotate by (argument_of_periapsis, inclination, longitude_ascending_node),
    # then heliocentric-ecliptic -> ICRS via astropy.coordinates frame transform.
    #
    # near-parabolic (perihelion_time set, mean_anomaly is None): solve
    # Barker's equation instead of Kepler's equation for the anomaly step.
    ...
```

---

## Phase 6: Background Task

### 6.1 New `_track_body_refresh` task on BaseTelescope

Registered via `add_background_task` in `__init__`. Runs continuously but sleeps long when idle; wakes to refresh when a body is being tracked.

```python
async def _track_body_refresh(self) -> None:
    await asyncio.sleep(10)
    while True:
        if self._tracked_body is None and self._tracked_elements is None:
            await asyncio.sleep(5)
            continue

        try:
            now = Time.now()
            if self._tracked_body is not None:
                # Horizons observer-table query already returns rate columns
                # (dRA*cosDec/dt, dDec/dt) alongside position for the same
                # epoch -- one query gives both, no finite-difference needed
                # here (see design doc, "Recompute cadence").
                ra, dec, ra_rate, dec_rate = await self._resolve_body_with_rate(self._tracked_body, now)
            else:
                # Two-body propagation has no closed-form rate output, so
                # finite-difference it locally (cheap -- no network call).
                ra, dec = self._propagate_elements(self._tracked_elements, now)
                dt = 1.0
                ra2, dec2 = self._propagate_elements(self._tracked_elements, now + dt)
                ra_rate = (ra2 - ra) * 3600 / dt   # arcsec/s
                dec_rate = (dec2 - dec) * 3600 / dt

            # Apply rate directly (bypass public entry point's mode check)
            if isinstance(self, ITrackingRate):
                await self._set_tracking_rate(ra_rate, dec_rate)
                await self.comm.set_state(ITrackingRate, TrackingRateState(ra_rate=ra_rate, dec_rate=dec_rate))

            # Periodic position nudge (every ~10 min)
            # ...

        except Exception:
            log.exception("Error in tracking refresh")

        sleep_interval = self._tracking_refresh_interval()
        await asyncio.sleep(sleep_interval)
```

### 6.2 Cadence logic

- Default: 600s (10 min) for planets/asteroids
- Moon-via-`ITrackingRate` fallback: 60s
- NEO close-approach: shorter (user-configurable or auto-detected from rate magnitude)
- Actual interval: `max(accuracy_driven_interval, capabilities.min_update_interval)`

### 6.3 Locking

Uses `self._lock_moving` / `self._abort_move` shared with `move_radec`/`move_altaz`. The background task attempts to acquire the lock; if a slew is in progress, it skips its tick.

---

## Phase 7: Dependencies

### 7.1 `pyproject.toml`

No new dependency. Propagation (5.4) is hand-rolled on top of `numpy`/`astropy.coordinates`, already core deps. `astroquery` is already a core dependency (includes `jplhorizons`).

---

## Phase 8: DummyTelescope

Not optional — implement all four new interfaces on `DummyTelescope`. Without a concrete class implementing `ITrackingMode`, nothing in the codebase would ever exercise the `move_radec`/`move_altaz` mode-reset side effects added in 4.1/4.2, and without `IPointingBody`/`IPointingOrbitalElements` support there'd be no running module to point a GUI at while building the group box described in the design doc's "GUI" section. `DummyTelescope` becomes the reference implementation for all of this.

### 8.1 Class bases

```python
class DummyTelescope(
    BaseTelescope,
    IPointingRaDec,
    IPointingAltAz,
    IOffsetsRaDec,
    IFocuser,
    IFilters,
    IFitsHeaderBefore,
    ITemperatures,
    ITrackingMode,
    ITrackingRate,
    IPointingBody,
    IPointingOrbitalElements,
    FitsNamespaceMixin,
):
```

`IPointingBody`/`IPointingOrbitalElements` need **no method overrides at all**: `track_body`/`track_orbital_elements` are concrete on `BaseTelescope` itself (5.2/5.3), backed by the concrete, shared `_resolve_body`/`_propagate_elements` helpers (5.1/5.4) — those aren't per-driver hooks. Adding the two interfaces to the base tuple is the entire diff for that part. In particular, `track_body('moon')` resolves via `astropy.coordinates.get_body`, which ships with astropy and needs no network — so GUI/manual testing against `DummyTelescope` can call `track_body('moon')` or `track_body('mars')` and get a real, physically-correct slew and tracking rate through the exact same code path production telescopes use, no extra plumbing. (An arbitrary asteroid designation would still fall through to the Horizons network path, same as production — fine to use, just not offline-safe.)

`ITrackingMode` is different: `set_tracking_mode` stays abstract per-driver on purpose (mode-switching is fundamentally hardware-native, `BaseTelescope` can't supply a generic default), so `DummyTelescope` needs a real implementation to simulate a firmware mode register.

### 8.2 `__init__` additions

```python
self._tracking_modes = [TrackingMode.SIDEREAL, TrackingMode.SOLAR, TrackingMode.LUNAR, TrackingMode.OFF]
self._tracking_mode = TrackingMode.OFF
self._tracking_rate = (0.0, 0.0)   # arcsec/sec, distinct from self._drift_rate (see 8.5)
```

### 8.3 `set_tracking_mode` (implements the abstract `ITrackingMode` hook)

```python
async def set_tracking_mode(self, mode: TrackingMode, **kwargs: Any) -> None:
    if mode not in self._tracking_modes:
        raise ValueError(f"Mode {mode} not supported.")
    self._tracking_mode = mode
    await self.comm.set_state(ITrackingMode, TrackingModeState(mode=mode))
```

### 8.4 `_set_tracking_rate` (implements the abstract per-driver hook from 4.3)

```python
async def _set_tracking_rate(self, ra_rate: float, dec_rate: float) -> None:
    self._tracking_rate = (ra_rate, dec_rate)
```

State publishing for `ITrackingRate` already happens in `BaseTelescope.set_tracking_rate` (4.4) and the background task (6.1) — no duplicate publish needed here; this hook is purely "apply to the simulated hardware."

### 8.5 Make the rate visible in the simulation

Without this, `set_tracking_rate`/`track_body` would accept calls and publish `ITrackingRate` state, but nothing would actually move — defeating the point of having a dummy to watch in a GUI. Extend `_move_task`'s idle (`else`, not-slewing) branch to apply `self._tracking_rate` to the real position:

```python
else:
    if self._tracking_rate != (0.0, 0.0):
        dra = self._tracking_rate[0] * u.arcsec / np.cos(np.radians(self._position.dec.degree))
        ddec = self._tracking_rate[1] * u.arcsec
        self._position = SkyCoord(ra=self._position.ra + dra, dec=self._position.dec + ddec, frame="icrs")
        await self.comm.set_state(
            IPointingRaDec,
            RaDecState(ra=float(self._position.ra.degree), dec=float(self._position.dec.degree)),
        )
    drift_ra = random.gauss(self._drift_rate[0], max(self._drift_rate[0] / 10.0, 1e-9))
    ...
```

Kept deliberately separate from the existing `self._drift`/`self._drift_rate` (simulated pointing-accuracy error, configurable at construction, used by autoguiding tests) rather than reusing that field: the two represent different simulated phenomena — one is "the mount doesn't quite point where it thinks," the other is "the target is actually moving across the sky" — and conflating them under one variable would make existing drift-based tests and new tracking-rate behavior fight over the same state. The loop already ticks once per second, so an `arcsec/sec` rate applies directly with no extra scaling.

### 8.6 Initial state/capabilities in `open()`

```python
await self.comm.set_capabilities(ITrackingMode, TrackingModeCapabilities(modes=self._tracking_modes))
await self.comm.set_capabilities(ITrackingRate, TrackingRateCapabilities(min_update_interval=0.0))
await self.comm.set_state(ITrackingMode, TrackingModeState(mode=self._tracking_mode))
await self.comm.set_state(
    ITrackingRate, TrackingRateState(ra_rate=self._tracking_rate[0], dec_rate=self._tracking_rate[1])
)
```

`min_update_interval=0.0` — a dummy has no protocol floor to simulate.

---

## Files Changed Summary

| File | Action |
|---|---|
| `pyobs/utils/enums.py` | Add `ARCSEC_PER_SEC` and `AU` to `Unit` |
| `pyobs/interfaces/ITrackingMode.py` | **New** |
| `pyobs/interfaces/ITrackingRate.py` | **New** |
| `pyobs/interfaces/IPointingBody.py` | **New** |
| `pyobs/interfaces/IPointingOrbitalElements.py` | **New** |
| `pyobs/interfaces/__init__.py` | Import + export new interfaces |
| `pyobs/modules/telescope/basetelescope.py` | Tracking-mode resets, `_set_tracking_rate`, `set_tracking_rate`, `track_body`, `track_orbital_elements`, background task |
| `pyobs/modules/telescope/dummytelescope.py` | Implement new abstract methods |

---

## Open Items / Risks

1. **Horizons rate limits** — queueing many asteroid targets per night may hit JPL rate limits. The 10-min refresh cadence helps but isn't guaranteed per-target.
2. **Two-body propagation accuracy** — hand-rolled two-body propagation ignores perturbations, same as any two-body library would. Fine for one night, drifts if elements are stale by weeks.
3. **Background task crash guard** — `BackgroundTask` considers >3 crashes in 10s as thrashing and calls `quit()`. The tracking task must be robust against transient errors (network failures for Horizons, etc.).
4. **Kepler solver edge cases** — Newton–Raphson on Kepler's equation converges slowly (or not at all with a naive iteration) as `e` approaches 1; the near-parabolic/cometary path must branch to Barker's equation rather than pushing eccentric-orbit iteration into a regime it's not designed for.
5. **No automatic path for brand-new NEOCP objects** — dropping MPC/NEOCP lookup means `track_body` has no way to resolve a bare designation for something too new for Horizons to have ingested; the caller must obtain elements themselves (MPC posting, NEOCP page) and call `track_orbital_elements` directly. Accepted trade-off, not a bug — see design doc's "Elements source" section.
