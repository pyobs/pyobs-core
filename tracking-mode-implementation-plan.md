# Non-Sidereal Tracking: Implementation Plan

## Overview

Four new interfaces (`ITrackingMode`, `ITrackingRate`, `IPointingBody`, `IPointingOrbitalElements`), modifications to `BaseTelescope`, one new enum member, two new dependencies, and a background task for continuous rate/position refresh.

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
    2. MPC/NEOCP lookup by designation — fetches orbital elements,
       then propagates locally via poliastro
    3. JPL Horizons fallback — anything not covered above
    """
```

- Step 1: `astropy.coordinates.get_body(body, Time.now(), observer=...)` -> SkyCoord -> (ra, dec)
- Step 2: MPC/NEOCP lookup — query `https://www.minorplanetcenter.net/` or `https://ssd.jpl.nasa.gov/api/horizons.api` for elements, construct `OrbitalElements`, propagate locally via poliastro
- Step 3: `astroquery.jplhorizons` Horizons class — query by name, get RA/Dec

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

Uses `poliastro`:

```python
from poliastro.bodies import Sun
from poliastro.twobody import Orbit
```

Keplerian propagation from orbital elements.

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
                ra, dec = await self._resolve_body(self._tracked_body)
            else:
                ra, dec = self._propagate_elements(self._tracked_elements, now)

            # Compute differential rate (1s finite difference)
            dt = 1.0
            if self._tracked_body is not None:
                ra2, dec2 = await self._resolve_body_at(self._tracked_body, now + dt)
            else:
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

Add to core `dependencies`:

```toml
"poliastro>=0.17,<0.18",
```

`astroquery` is already a core dependency (includes `jplhorizons`).

---

## Phase 8: DummyTelescope

### 8.1 `pyobs/modules/telescope/dummytelescope.py`

Implement the new abstract methods:

- `_set_tracking_rate(ra_rate, dec_rate)` — store values, publish state
- Optionally implement `ITrackingMode` for testing
- Optionally implement `IPointingBody` / `IPointingOrbitalElements` for testing

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
| `pyproject.toml` | Add `poliastro` dependency |

---

## Open Items / Risks

1. **Horizons rate limits** — queueing many asteroid targets per night may hit JPL rate limits. The 10-min refresh cadence helps but isn't guaranteed per-target.
2. **Two-body propagation accuracy** — `poliastro` two-body ignores perturbations. Fine for one night, drifts if elements are stale by weeks.
3. **MPC/NEOCP API stability** — the Minor Planet Center doesn't have a formal REST API; scraping may break. Horizons is the more stable fallback.
4. **Background task crash guard** — `BackgroundTask` considers >3 crashes in 10s as thrashing and calls `quit()`. The tracking task must be robust against transient errors (network failures for Horizons, etc.).
