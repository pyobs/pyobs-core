# Non-Sidereal Tracking: Interface Design

## Problem

`IPointing*` interfaces (`IPointingRaDec`, `IPointingAltAz`, `IPointingHGS`, `IPointingHelioprojective`) only express "go to this coordinate." What happens once the telescope is there — sidereal tracking, solar tracking — is currently implicit in whichever driver/module class is running, not addressable at runtime. `BaseTelescope.move_radec` (`pyobs/modules/telescope/basetelescope.py`) slews and sets `MotionStatus.TRACKING`, but the actual tracking rate is baked into `_move_radec`'s hardware implementation. `move_altaz`, by contrast, ends in `MotionStatus.POSITIONED` — that distinction already exists and is deliberate; alt/az is "point here and hold," not a tracking frame.

We want to support tracking the Moon, planets, asteroids/comets, and other solar-system bodies at runtime, without hardcoding tracking behavior per telescope class.

## Design principle: pointing interfaces stay pointing-only

Pointing interfaces (`IPointingRaDec`, `IPointingAltAz`, `IPointingHGS`, `IPointingHelioprojective`) and tracking interfaces (`ITrackingMode`, `ITrackingRate`) are kept strictly separate at the interface level. No pointing method takes a tracking-related parameter — `move_radec(ra, dec, **kwargs)` and `move_altaz(alt, az, **kwargs)` keep their contracts exactly as they are today, "go to this coordinate," nothing else.

That said, each coordinate frame does imply a natural default tracking behavior once the telescope arrives there:

| Interface | Natural tracking behavior | Mechanism |
|---|---|---|
| `IPointingRaDec` | sidereal | discrete `TrackingMode.SIDEREAL` |
| `IPointingAltAz` | hold fixed alt/az → no motion | discrete `TrackingMode.OFF` |
| `IPointingHGS` / `IPointingHelioprojective` | solar | discrete `TrackingMode.SOLAR` |
| `IPointingBody` / `IPointingOrbitalElements` | follow computed ephemeris | continuous `ITrackingRate`, fed by a background task |

The first three resolve to a **discrete `TrackingMode`** and are applied as an internal side effect inside `BaseTelescope`'s concrete implementation — not as a parameter on the abstract interface method. This is the same category of thing as `move_radec` already setting `MotionStatus.TRACKING` as a side effect: documented behavior of the concrete class, not a hidden argument, and not part of the interface's public signature.

```python
# BaseTelescope
@timeout(1200)
async def move_radec(self, ra: float, dec: float, **kwargs: Any) -> None:
    ...
    if isinstance(self, ITrackingMode):
        await self.set_tracking_mode(TrackingMode.SIDEREAL)
    await self._move_radec(ra, dec, abort_event=self._abort_move)
    ...

@timeout(1200)
async def move_altaz(self, alt: float, az: float, **kwargs: Any) -> None:
    ...
    if isinstance(self, ITrackingMode):
        await self.set_tracking_mode(TrackingMode.OFF)
    await self._move_altaz(alt, az, abort_event=self._abort_move)
    ...
```

This fixes a real bug, not just a style preference: without the reset, a mount left in lunar/custom-rate mode from a previous target would silently keep applying the stale rate after a plain `move_radec(ra, dec)` to an unrelated sidereal target — a slow, hard-to-notice drift rather than a loud failure. The `move_altaz` case is the same risk in the opposite direction: pointing at a flat-field screen after tracking the Moon must not leave residual lunar rate applied while sitting at that alt/az.

`move_hgs_lon_lat`/`move_helioprojective` would get the equivalent reset to `TrackingMode.SOLAR` for symmetry — worth adding only once a concrete solar-telescope class implements `ITrackingMode` with more than one option; if it only ever does solar tracking, there's nothing to default away from.

The fourth row, bodies/orbital elements, is fundamentally different and does **not** go through `TrackingMode` at all — there's no `TrackingMode.PLANET` or `TrackingMode.ASTEROID` in the enum, and there won't be one. It's "keep feeding `set_tracking_rate` forever," which is why it needs the background task described below rather than a one-shot mode switch.

**Explicit tracking-mode changes** (switching mode without moving, turning tracking `OFF` without parking, or a caller wanting `LUNAR`/`SOLAR` outside of `track_body`) always go through `ITrackingMode.set_tracking_mode()` directly — a separate, explicit call, never bundled into a pointing call.

## Design: two orthogonal tracking interfaces

Hardware capability splits along a real seam, confirmed by the ASCOM standard (relevant since our Celestron mount is likely reached via `pyobs-alpaca`): ASCOM's `ITelescope` exposes a discrete `TrackingRate` enum (`driveSidereal`/`driveLunar`/`driveSolar`/`driveKing`) *and* separate continuous `RightAscensionRate`/`DeclinationRate` offset properties. Two interfaces map directly onto that:

- **`ITrackingMode`** — discrete, firmware-native tracking rates (sidereal/solar/lunar/off). A driver implements this only if the hardware actually has these modes.
- **`ITrackingRate`** — an arbitrary continuous RA/Dec rate offset, for anything without a native mode (planets, comets, asteroids, arbitrary bodies). pyobs-core computes the rate from ephemeris and pushes it down periodically.

Splitting them lets a driver implement only what it can, rather than forcing every backend to fake support for modes it doesn't have. Orbital-element/body tracking is **not** a third tracking primitive — it's an ephemeris *source* that feeds into `ITrackingRate` via the background task described below.

### `ITrackingMode`

```python
# pyobs/interfaces/ITrackingMode.py
from __future__ import annotations
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ..utils.time import Time
from .interface import Interface


class TrackingMode(StrEnum):
    SIDEREAL = "sidereal"
    SOLAR = "solar"
    LUNAR = "lunar"
    OFF = "off"


@dataclass
class TrackingModeState:
    mode: TrackingMode
    time: Time = field(default_factory=Time.now)


@dataclass
class TrackingModeCapabilities:
    modes: list[TrackingMode]


class ITrackingMode(Interface, metaclass=ABCMeta):
    """The module supports switching between discrete, hardware-native tracking rates."""

    __module__ = "pyobs.interfaces"

    state = TrackingModeState
    capabilities = TrackingModeCapabilities

    @abstractmethod
    async def set_tracking_mode(self, mode: TrackingMode, **kwargs: Any) -> None:
        """Switches to the given tracking mode.

        Args:
            mode: Tracking mode to switch to.

        Raises:
            MoveError: If mode could not be set.
            ValueError: If mode is not in this module's capabilities.
        """
        ...


__all__ = ["ITrackingMode", "TrackingMode", "TrackingModeState", "TrackingModeCapabilities"]
```

### `ITrackingRate`

```python
# pyobs/interfaces/ITrackingRate.py
from __future__ import annotations
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


@dataclass
class TrackingRateState:
    ra_rate: Annotated[float, Unit.ARCSEC_PER_SEC]
    dec_rate: Annotated[float, Unit.ARCSEC_PER_SEC]
    time: Time = field(default_factory=Time.now)


@dataclass
class TrackingRateCapabilities:
    min_update_interval: Annotated[float, Unit.SECONDS]
    """Minimum time between successive set_tracking_rate calls this hardware/protocol accepts,
    independent of whether the value actually changed. Populated per-driver from whatever its
    protocol allows; 0 if the hardware has no such floor."""


class ITrackingRate(Interface, metaclass=ABCMeta):
    """The module accepts an arbitrary non-sidereal tracking rate as an absolute RA/Dec offset."""

    __module__ = "pyobs.interfaces"

    state = TrackingRateState
    capabilities = TrackingRateCapabilities

    @abstractmethod
    async def set_tracking_rate(
        self,
        ra_rate: Annotated[float, Unit.ARCSEC_PER_SEC],
        dec_rate: Annotated[float, Unit.ARCSEC_PER_SEC],
        **kwargs: Any,
    ) -> None:
        """Sets an absolute tracking rate on the sky, in arcsec/sec.

        Args:
            ra_rate: Rate in RA, arcsec/sec on the sky.
            dec_rate: Rate in Dec, arcsec/sec on the sky.

        Raises:
            MoveError: If rate could not be set.
        """
        ...


__all__ = ["ITrackingRate", "TrackingRateState", "TrackingRateCapabilities"]
```


Rate is defined as **absolute arcsec/sec on the sky** at the interface level, not offset-from-sidereal. This is the physically correct abstraction for what the background task computes: RA/Dec are sky-fixed coordinates, so a body's d(RA)/dt, d(Dec)/dt from ephemeris differencing is an absolute, mount-independent quantity, completely separate from whatever tracking mode happens to be active. It also keeps `Unit.ARCSEC_PER_SEC` meaningful regardless of backend. ASCOM's `RightAscensionRate` is specified in seconds-of-RA per sidereal second and is defined as an *offset from the current `TrackingRate`* — that conversion (delta = absolute_rate − sidereal_rate, × the sidereal/solar second ratio, ≈1.0027379) is ASCOM-specific and belongs in the driver implementing this interface, not in the interface itself.

### Required base mode: `SIDEREAL`, not `OFF`

A rate set via `ITrackingRate` must be applied on top of `TrackingMode.SIDEREAL`, never `OFF`. This isn't an arbitrary choice — everything tracked via `ITrackingRate` (Moon, planets, asteroids, comets) moves across the sky at a rate dominated by Earth's rotation and only slightly perturbed by the body's own orbital motion, so "sidereal plus a small correction" is the actual physical decomposition of the motion, not just an API convention. `OFF` would mean the rate has to represent the *entire* sidereal-scale motion rather than a small correction, defeating the purpose of having a base mode, and on hardware where the rate register is defined as a delta from the base rate (as on ASCOM), there may be no way to represent an absolute rate correctly against an `OFF` base at all.

Given that, `ITrackingRate.set_tracking_rate` is not purely a pass-through to hardware — it has a precondition to enforce. `BaseTelescope` mirrors the existing `move_radec`/`_move_radec` split (public method does locking/checks/side-effects, abstract private method is the actual per-driver hardware call) for this too:

```python
class ITrackingRate(Interface, metaclass=ABCMeta):
    state = TrackingRateState

    @abstractmethod
    async def set_tracking_rate(self, ra_rate: float, dec_rate: float, **kwargs: Any) -> None:
        ...
```

```python
# BaseTelescope
@abstractmethod
async def _set_tracking_rate(self, ra_rate: float, dec_rate: float) -> None:
    """Actually applies the rate to hardware. Implemented by concrete driver classes."""
    ...

async def set_tracking_rate(self, ra_rate: float, dec_rate: float, **kwargs: Any) -> None:
    """Public entry point for external/manual callers. Enforces the SIDEREAL precondition."""
    if isinstance(self, ITrackingMode):
        current = self.comm.get_own_state(ITrackingMode)
        if current is None or current.mode != TrackingMode.SIDEREAL:
            await self.set_tracking_mode(TrackingMode.SIDEREAL)
    await self._set_tracking_rate(ra_rate, dec_rate)
    await self.comm.set_state(ITrackingRate, TrackingRateState(ra_rate=ra_rate, dec_rate=dec_rate))
```

`self.comm.get_own_state`/`self.comm.set_state` — not `self.get_state`/`self.set_state`, which are a different pair of methods (the former is the read side of a *remote proxy's* subscribed state and always returns `None` for `self`; the latter is `Module.set_state`, which sets module lifecycle state, not interface state).

The public `set_tracking_rate` checks current mode via the already-subscribed `ITrackingMode` state (no extra round-trip, it's pub-sub) and only issues a `set_tracking_mode(SIDEREAL)` call if not already there — avoiding an unnecessary hardware mode-switch command on every call, which matters on mounts where a mode switch is an actual relay/gear change rather than a register write.

The body/orbital-element background task (below), running inside `BaseTelescope` itself, calls `_set_tracking_rate` directly on every cycle, bypassing the mode check entirely. This isn't just a performance shortcut: the background task already established `SIDEREAL` once, as a side effect of the initial `move_radec` call that `track_body`/`track_orbital_elements` issued to slew there. If the task re-checked and re-enforced mode on every single cycle, it would also silently fight and override any *external* `set_tracking_mode` call a user makes mid-track — which is wrong; if someone deliberately switches mode away from `SIDEREAL` while a body is being tracked, that's their explicit action and the background task shouldn't stomp on it every 5–10 seconds. So the precondition is enforced once, at the trusted entry point that establishes it, not repeatedly by an internal caller that already relies on it holding.

**Scope decision — RA/Dec only, deliberately.** No other rate kind is needed. LEO satellite tracking was considered and explicitly excluded: none of our telescopes can slew/react fast enough to make it meaningful, and a real satellite-tracking approach wouldn't fit `ITrackingRate` anyway (angular velocity changes too fast for a rate-and-extrapolate model near zenith passage; would need high-frequency position streaming instead of a rate). Field/parallactic rotation rate was also considered and is out of scope here: our telescopes with a derotator already derive derotator angle from current alt/az position, not from tracking rate, so there's no dependency between `ITrackingRate` and derotation at all.

## `IPointingBody` — convenience layer for named bodies

```python
# pyobs/interfaces/IPointingBody.py
class IPointingBody(Interface, metaclass=ABCMeta):
    """Points at and tracks a named solar-system body."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def track_body(self, body: str, **kwargs: Any) -> None:
        """Starts tracking a named solar-system body.

        Args:
            body: Name resolvable to an ephemeris (e.g. 'moon', 'mars', 'jupiter', or an
                  asteroid/comet designation — see resolution strategy below).

        Raises:
            MoveError: If telescope could not be moved.
            ValueError: If body name is not resolvable.
        """
        ...
```

Composes `IPointingRaDec` + `ITrackingMode`/`ITrackingRate` under the hood, and internally calls `set_tracking_mode`/`set_tracking_rate` as appropriate for the resolved body. **This is the only path for tracking the Moon, planets, asteroids, or comets** — there is deliberately no `tracking_mode` value or parameter anywhere for these; a caller who wants to track the Moon calls `track_body('moon')`, full stop. `move_radec` is never used directly for this purpose (a caller manually computing a body's RA/Dec and calling `move_radec` + `set_tracking_mode(LUNAR)` themselves would just be duplicating what `track_body` already does).

## Asteroids/comets: ephemeris sources, not a new tracking primitive

Orbital elements don't belong on `ITrackingMode` (no mount firmware understands six orbital elements — that interface is strictly discrete/firmware-native) and a bare `set_tracking_rate` call isn't sufficient by itself either, since a rate is only the instantaneous output of propagating elements — something still has to do that propagation continuously as geometry changes over a sequence. Both routes below feed the same background task and the same `ITrackingRate` consumer; they differ only in where the ephemeris comes from.

**Option A — extend `IPointingBody.track_body(body: str)` resolution.** Try `astropy.coordinates.get_body` first (Sun/Moon/major planets); for anything not found there, resolve via JPL Horizons (`astroquery.jplhorizons`) instead. No interface change — same call, same signature. Horizons ephemeris is perturbation-aware and accurate.
- Trade-off: network dependency per target, possible rate-limiting when queueing several asteroid pointings in one night, and no coverage for objects newer than Horizons' latest ingest — exactly the case where speed matters most (fast NEO follow-up). That gap is accepted rather than patched with an automatic MPC/NEOCP lookup (see "Elements source" below); it's covered by calling `track_orbital_elements` directly instead.

**Option B — dedicated interface taking orbital elements directly:**

```python
@dataclass
class OrbitalElements:
    epoch: Time
    semi_major_axis: Annotated[float, Unit.AU]
    eccentricity: float
    inclination: Annotated[float, Unit.DEGREES]
    longitude_ascending_node: Annotated[float, Unit.DEGREES]
    argument_of_periapsis: Annotated[float, Unit.DEGREES]
    mean_anomaly: Annotated[float, Unit.DEGREES] | None = None   # elliptical
    perihelion_time: Time | None = None                          # comets/near-parabolic

class IPointingOrbitalElements(Interface, metaclass=ABCMeta):
    """Points at and tracks a body defined by orbital elements (asteroid, comet, NEO)."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def track_orbital_elements(self, elements: OrbitalElements, **kwargs: Any) -> None:
        ...
```

Propagation happens locally, hand-rolled rather than via a third-party orbital-mechanics library — no network round-trip — and feeds the exact same background task and `set_tracking_rate` path as `IPointingBody`.

**Why hand-rolled, not a library.** The obvious dependency, `poliastro`, doesn't actually work here: its last release (0.17.0, 2022) requires `python>=3.8,<3.11` and `astropy>=5.0,<6`, both incompatible with this project's `python>=3.11` / `astropy>=7.0.1,<9` — pip cannot resolve it at all, on any supported Python version. Its actively-maintained fork, `hapsira`, would resolve, but drags in `matplotlib`, `numba`, and `plotly` transitively for a feature that only ever needs a position at a handful of timestamps, never a plot. Given that two-body propagation is only ever "good for one night" here regardless of implementation (see trade-off below), a full orbital-mechanics library buys negligible extra correctness in exchange for a heavy, awkward-to-pin dependency. Classical two-body Kepler propagation is a small, textbook computation, implemented directly with `numpy` + `astropy.coordinates` — both already core dependencies, nothing new to add.

Propagation, elliptical case (`mean_anomaly` given):
1. Mean motion `n = k · a^(-3/2)` (Gaussian gravitational constant `k = 0.01720209895` rad/day, `a` in AU) — the standard heliocentric two-body relation; `k` already encodes the Sun's GM for elements expressed this way, so no per-body mass lookup is needed.
2. Mean anomaly at time `t`: `M(t) = mean_anomaly + n · (t − epoch)`.
3. Solve Kepler's equation `M = E − e·sin(E)` for eccentric anomaly `E` via Newton–Raphson — a handful of iterations converges to double precision for all but near-parabolic `e`.
4. True anomaly and heliocentric distance from `E` via the standard closed-form relations.
5. Position in the perifocal (orbital) plane, then three rotations (argument of periapsis, inclination, longitude of ascending node) into heliocentric ecliptic Cartesian coordinates.
6. Heliocentric ecliptic → ICRS via `astropy.coordinates` frame transforms (handles the ecliptic-to-equatorial rotation and Earth's own position, so the result comes out as a normal geocentric `SkyCoord`), then RA/Dec straight off that.

Near-parabolic/cometary case (`perihelion_time` given, `mean_anomaly` absent): step 2's linear-in-mean-anomaly form breaks down as `e → 1`, so this path solves Barker's equation (or a universal-variable formulation) instead of Kepler's equation at step 3. More fiddly than the elliptical case, but still self-contained — no new dependency either way.

**Benchmark.** Measured directly rather than assumed, since "hand-rolled" invites the question of whether it's actually cheap enough: steps 1–5 (Kepler solve + rotations, pure numpy, no astropy) cost **~6 µs/call**. Step 6 (the `astropy.coordinates` heliocentric-ecliptic → ICRS frame transform) dominates completely at **~1.2 ms/call** warm — three orders of magnitude more than the orbit math itself, all of it astropy's `SkyCoord`/frame-transform bookkeeping rather than anything intrinsic to the propagation. A cold first call in a fresh process (imports, IERS table init) costs ~270 ms, but that's paid once per process lifetime, not per tick. At the background task's 60–600s cadence and at most two calls per tick (position + one finite-difference sample for rate), total cost is ~2 ms every 60s in the worst case — not a design concern, and irrelevant next to the lock-contention/slew-timing questions raised elsewhere in this doc.

- Trade-off: no network dependency, works for elements minutes-old off a freshly-posted orbital-element set, but two-body propagation ignores perturbations regardless of whether it's hand-rolled or library-based — fine over one night's arc, would drift if elements are stale by weeks.

**Elements source: manual only, no automatic MPC/NEOCP lookup.** `track_orbital_elements(elements: OrbitalElements)` **is** the entry point for anything with orbital elements in hand — typed in, pasted from an MPC/NEOCP posting, whatever the source. There is deliberately no automatic scraping layer built on top of it, resolving a designation to elements the way `track_body` resolves a name to a position.

An automatic MPC/NEOCP-by-designation step, folded into `track_body`'s resolution chain, was considered and dropped: the Minor Planet Center has no formal REST API, so "automatic lookup" would mean scraping an unversioned web page — and doing that is riskiest precisely for a NEOCP object posted hours ago, the one case (fast NEO follow-up) this whole feature exists to unblock. A scraper silently breaking on exactly that object, at exactly the moment speed matters most, is a worse failure mode than not having the automation at all. Manual entry doesn't lose capability here, only the one-call convenience of typing a designation instead of pasting the six element values — and it's more robust, since it never depends on a page MPC could restructure at any time.

`track_body`'s resolution chain is therefore just two steps:

```python
async def track_body(self, body: str, **kwargs: Any) -> None:
    # 1. astropy get_body — Sun, Moon, major planets
    # 2. Horizons fallback — anything not covered above
```

## Where the ephemeris/propagation math lives

Centralized in `pyobs-core`, not per-driver. `BaseTelescope` already runs a background task, `_celestial` (`pyobs/modules/telescope/basetelescope.py`), recomputing moon/sun altaz and separation every 30s for FITS headers. Add a sibling background task that, while a body or orbital-element target is being tracked:

1. Recomputes the target's current RA/Dec (via `get_body`/Horizons for `IPointingBody`, or local two-body propagation for `IPointingOrbitalElements`).
2. Computes a differential RA/Dec rate (finite difference over a short interval, or analytic where available).
3. Dispatches based on capabilities:
   - Sun/Moon **and** driver implements `ITrackingMode` with that mode in its `TrackingModeCapabilities` → `set_tracking_mode`.
   - Otherwise, if driver implements `ITrackingRate` → `_set_tracking_rate` (the internal primitive, bypassing the public entry point's mode check — see below) with the computed offset, plus periodic `move_radec` nudges to correct accumulated drift.
   - Neither → not trackable on this hardware; raise/log clearly rather than silently drifting.

See "Recompute cadence" below for how often step 1–3 should actually run.

## Manual/advanced callers using `ITrackingRate`/`ITrackingMode` directly

Tracking mode/rate is a live mount property, not something latched at slew-time (mirrors ASCOM: `TrackingRate`/`RightAscensionRate`/`DeclinationRate` can change anytime and take effect immediately). So `set_tracking_rate()` → `move_radec()` and the reverse order both end up correct once both calls land. Recommended order is still "set tracking before slewing," purely to avoid a multi-second window right after slew completion where the mount tracks at the just-reset default (sidereal, or off) before an explicit tracking call arrives — cosmetic in general, but matters for exposures starting immediately after slew.

## GUI

A separate group box, not folded into the existing RA/Dec pointing widget, shown only if the module actually implements `ITrackingMode`/`ITrackingRate`/`IPointingBody` — mirrors how `IAutoFocus`/`IAutoGuiding` widgets already only appear when the interface is present. Contents:

- Dropdown of discrete modes, populated from the subscribed `TrackingModeCapabilities` (not hardcoded, so it only offers what this specific mount supports).
- A "track body" field/dropdown for named solar-system bodies if `IPointingBody` is present.
- A read-only current-mode/rate display driven by the subscribed `ITrackingMode`/`ITrackingRate` state — same live-subscription pattern as the rest of pyobs-gui post-2.0, no polling.

## Recompute cadence

Rate and position refresh are decoupled — they don't need the same cadence, because what actually determines staleness differs between them:

- **Rate**, applied continuously via `_set_tracking_rate` between refreshes, only goes stale as fast as the target's angular *acceleration* changes it — not its angular velocity. For the Moon, main-belt asteroids, and planets, that's a slowly-varying quantity: a rate computed from elements/ephemeris up to ~10 minutes old is still accurate enough to apply continuously in between, since the rate itself hasn't meaningfully changed over that window.
- **Position** is only actually consumed at two moments: the initial slew (via `track_body`'s `move_radec` call) and the periodic drift-correction nudge that corrects the small error accumulated from rate-only tracking between refreshes. It doesn't need to be fresher than the resync interval calls for, and can run on its own, coarser schedule independent of rate refresh.

For Option A (Horizons), a single query per refresh interval covers both needs at once — Horizons' observer-table output already includes RA/Dec rate columns (dRA·cosDec/dt, dDec/dt) directly alongside position for a given epoch, so no finite-differencing between separate position queries is needed. This also keeps network load reasonable: one call per target per ~10 minutes rather than per-cycle, which matters once multiple asteroid targets are queued across a night given Horizons' rate limits.

**Default: 10 minute rate/position refresh for most targets, locally interpolated in between — but this needs to scale down for fast-apparent-motion bodies rather than apply as one flat constant.** Checked with real apparent-rate numbers (computed for 2026-07-13, from Hannover) rather than asserted: rate at t=0, and the position error that would accumulate if that rate were held constant, unrefreshed, for a full 10 minutes.

| Body | rate (arcsec/s) | error after 10 min of stale rate |
|---|---|---|
| Mars | 0.029 | 0.001″ |
| Venus | 0.042 | 0.005″ |
| Jupiter | 0.009 | 0.001″ |
| Moon | 0.77 | 0.4–0.6″ |

Planets and main-belt asteroids (which are Mars-scale-or-slower in apparent motion for most geometries) land in the negligible bucket — a 10 minute refresh interval leaves them accurate to well under a milliarcsecond, three orders of magnitude below anything that matters. The **Moon is a genuinely different scale**: 0.4–0.6″ of accumulated drift over 10 minutes, non-negligible against typical seeing (1–3″) for careful photometry or fine guiding. This doesn't threaten the 10-minute default in practice, though, since the Moon is exactly the case routed through native `TrackingMode.LUNAR` (not `ITrackingRate`) whenever the driver has it. It only matters as a real edge case on a mount *without* native lunar tracking, forced to fall back to `ITrackingRate` for the Moon specifically — there, the refresh interval should tighten to roughly 1 minute, which by the same linear approximation brings the error down to single-digit milliarcsec.

So: **10 min for planets/asteroids, ~1 min for a Moon-via-`ITrackingRate` fallback** — cadence keyed to the target's apparent rate magnitude (or simply per body-class) rather than one fixed constant applied uniformly. Close-approach NEOs remain the outlier requiring much tighter cadence still, and route through Option B as already established.

### Hardware update-rate floor

The cadence above is entirely accuracy-driven — how often the *value* needs to change to stay correct. That's a separate constraint from a protocol/hardware floor some mounts impose on how often a new rate can be sent at all, independent of whether the value changed (e.g. a mount that only accepts a new tracking-rate command every 10s). For nearly every case here the two don't conflict, since accuracy-driven intervals (minutes) are already far coarser than any 10s-scale hardware floor. The one case it does threaten is the close-approach NEO path (Option B, needs 1–2s), where a slow hardware floor means that target genuinely can't be tracked accurately regardless of how good the local propagation is — that should surface as an explicit capability limitation, not silently degrade into resending a stale rate faster than the hardware will accept it.

`TrackingRateCapabilities.min_update_interval` (added above) exposes this per-driver. The background task computes its actual refresh interval as `max(accuracy_driven_interval, capabilities.min_update_interval)`; if that maximum ends up coarser than what the target's accuracy actually needs, the caller should be told this mount can't track that target well enough, rather than the scheduler quietly accepting degraded tracking.

## Locking

Resolved: the background task's rate/position refresh **shares** `_lock_moving`/`_abort_move` with `move_radec`/`move_altaz`, rather than using a separate lock. Two reasons, not just caution:

- **Ordering correctness.** `move_radec`/`move_altaz` reset `TrackingMode` (to `SIDEREAL`/`OFF`) as a side effect the moment a slew starts. Without a shared lock, a concurrent rate update from the background task could race that reset and land on the wrong side of it — applied against whichever mode happened to be active at that instant rather than the one the slew is establishing.
- **Single command channel.** Most mount protocols are one serial/network channel; two async tasks issuing commands concurrently risks interleaved or garbled writes at the protocol level, independent of tracking logic entirely. One lock around all mount-directed commands is the safer default regardless.

One consequence worth noting rather than treating as a bug: `move_radec` carries `@timeout(1200)` (`pyobs/modules/telescope/basetelescope.py`) — a slow slew plus dome-wait can hold the lock for up to 20 minutes, during which the background task simply skips its tick(s). That's correct behavior (nothing should be actively rate-tracking during a slew), and the periodic resync nudge after the slew completes absorbs whatever gap accumulated. It does mean the stated refresh cadence (10 min / 1 min / etc.) is a target, not a hard guarantee — actual cadence is "as specified, or until the current move finishes, whichever is later."