from __future__ import annotations

import asyncio
import logging
import math
from abc import ABCMeta, abstractmethod
from typing import Any

import astropy.units as u
from astropy.coordinates import ICRS, HeliocentricMeanEcliptic, SkyCoord, get_body
from astroquery.jplhorizons import Horizons

from pyobs.events import MoveAltAzEvent, MoveRaDecEvent
from pyobs.interfaces import (
    AltAzState,
    FitsHeaderEntry,
    IFitsHeaderBefore,
    IPointingAltAz,
    IPointingBody,
    IPointingOrbitalElements,
    IPointingRaDec,
    ITelescope,
    ITrackingMode,
    ITrackingRate,
    OrbitalElements,
    TrackingMode,
    TrackingRateState,
)
from pyobs.mixins import MotionStatusMixin, WaitForMotionMixin, WeatherAwareMixin
from pyobs.modules import Module, timeout
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import MotionStatus
from pyobs.utils.threads import LockWithAbort
from pyobs.utils.time import Time

log = logging.getLogger(__name__)

# Gaussian gravitational constant, rad/day, for AU/day/solar-mass units -- encodes the Sun's
# GM for heliocentric two-body elements, so no per-body mass lookup is needed.
_GAUSSIAN_GRAVITATIONAL_CONSTANT = 0.01720209895

# Default background-task refresh cadence for continuously-tracked bodies/elements. See design
# doc's "Recompute cadence" section: negligible position error over 10 min for anything at or
# below Mars/Venus/Jupiter-scale apparent motion; the Moon (fallback via ITrackingRate only, i.e.
# when no native TrackingMode.LUNAR is available) needs the tighter interval instead.
_DEFAULT_REFRESH_INTERVAL_SECONDS = 600.0
_MOON_FALLBACK_REFRESH_INTERVAL_SECONDS = 60.0

# How often to correct accumulated position drift with a direct hardware reslew, on top of the
# continuous rate updates applied every refresh tick.
_POSITION_NUDGE_INTERVAL_SECONDS = 600.0


def _solve_kepler_equation(mean_anomaly: float, eccentricity: float, tol: float = 1e-12, max_iter: int = 50) -> float:
    """Solves M = E - e*sin(E) for the eccentric anomaly E, via Newton-Raphson.

    Args:
        mean_anomaly: Mean anomaly, in radians (any range; wrapped internally).
        eccentricity: Orbital eccentricity (0 <= e < 1).
    """
    m = math.fmod(mean_anomaly, 2 * math.pi)
    e_anom = m if eccentricity < 0.8 else math.pi
    for _ in range(max_iter):
        delta = (e_anom - eccentricity * math.sin(e_anom) - m) / (1 - eccentricity * math.cos(e_anom))
        e_anom -= delta
        if abs(delta) < tol:
            break
    return e_anom


def _solve_barker_equation(mean_anomaly: float, tol: float = 1e-12, max_iter: int = 50) -> float:
    """Solves D + D**3/3 = M for D (Barker's equation, near-parabolic/cometary orbits).

    Unlike Kepler's equation, this cubic is globally monotonic (its derivative 1 + D**2 is
    always positive), so Newton-Raphson from any starting point converges reliably -- no
    near-e=1 convergence trouble the way the elliptical solver above can have.
    """
    d = mean_anomaly
    for _ in range(max_iter):
        delta = (d + d**3 / 3 - mean_anomaly) / (1 + d**2)
        d -= delta
        if abs(delta) < tol:
            break
    return d


def _perifocal_to_radec(
    x_pf: float,
    y_pf: float,
    argument_of_periapsis: float,
    inclination: float,
    longitude_ascending_node: float,
    t: Time,
) -> tuple[float, float]:
    """Rotates a perifocal-plane position into heliocentric ecliptic coordinates, then converts
    to ICRS RA/Dec via astropy's frame-transform machinery (which also applies the
    heliocentric -> geocentric shift for the given obstime).

    Args:
        x_pf: X position in the perifocal (orbital) plane, AU.
        y_pf: Y position in the perifocal (orbital) plane, AU.
        argument_of_periapsis: Degrees.
        inclination: Degrees.
        longitude_ascending_node: Degrees.
        t: Time of the position.
    """
    x3, y3, z3 = _orbital_plane_to_ecliptic_cartesian(
        x_pf, y_pf, argument_of_periapsis, inclination, longitude_ascending_node
    )
    coord = SkyCoord(
        x=x3 * u.AU,
        y=y3 * u.AU,
        z=z3 * u.AU,
        frame=HeliocentricMeanEcliptic(obstime=t),
        representation_type="cartesian",
    )
    icrs = coord.icrs
    return float(icrs.ra.degree), float(icrs.dec.degree)


def _orbital_plane_to_ecliptic_cartesian(
    x_pf: float, y_pf: float, argument_of_periapsis: float, inclination: float, longitude_ascending_node: float
) -> tuple[float, float, float]:
    """Rotates a perifocal-plane position (AU) into heliocentric ecliptic Cartesian coordinates
    (AU), via the standard classical-orbital-element rotation Rz(Om) @ Rx(i) @ Rz(w). Pure
    geometry, split out from _perifocal_to_radec so it's testable without astropy's frame
    machinery.
    """
    w = math.radians(argument_of_periapsis)
    i = math.radians(inclination)
    om = math.radians(longitude_ascending_node)
    cw, sw = math.cos(w), math.sin(w)
    ci, si = math.cos(i), math.sin(i)
    co, so = math.cos(om), math.sin(om)

    # Rz(w): rotate within the orbital plane from periapsis direction to ascending-node direction
    x1 = cw * x_pf - sw * y_pf
    y1 = sw * x_pf + cw * y_pf
    # Rx(i): tilt the orbital plane by the inclination
    y2 = ci * y1
    z2 = si * y1
    # Rz(Om): rotate the ascending node into the reference (ecliptic) frame
    x3 = co * x1 - so * y2
    y3 = so * x1 + co * y2
    z3 = z2

    return x3, y3, z3


def _propagate_elements(elements: OrbitalElements, t: Time) -> tuple[float, float]:
    """Two-body Kepler propagation of orbital elements to (ra, dec) in degrees, ICRS.

    Perturbations are ignored -- fine over one night's arc, would drift if elements are stale
    by weeks. See design doc's "Asteroids/comets" section for the derivation.
    """
    if elements.mean_anomaly is not None:
        # elliptical
        dt_days = (t - elements.epoch).jd
        n = _GAUSSIAN_GRAVITATIONAL_CONSTANT * elements.semi_major_axis**-1.5  # rad/day
        m = math.radians(elements.mean_anomaly) + n * dt_days
        e_anom = _solve_kepler_equation(m, elements.eccentricity)
        nu = 2 * math.atan2(
            math.sqrt(1 + elements.eccentricity) * math.sin(e_anom / 2),
            math.sqrt(1 - elements.eccentricity) * math.cos(e_anom / 2),
        )
        r = elements.semi_major_axis * (1 - elements.eccentricity * math.cos(e_anom))
    elif elements.perihelion_time is not None:
        # near-parabolic/cometary: Barker's equation, using perihelion distance q = a*(1-e)
        q = elements.semi_major_axis * (1 - elements.eccentricity)
        dt_days = (t - elements.perihelion_time).jd
        m_p = _GAUSSIAN_GRAVITATIONAL_CONSTANT * dt_days / math.sqrt(2 * q**3)
        d = _solve_barker_equation(m_p)
        nu = 2 * math.atan(d)
        r = q * (1 + d**2)
    else:
        raise ValueError("OrbitalElements must set either mean_anomaly or perihelion_time.")

    x_pf = r * math.cos(nu)
    y_pf = r * math.sin(nu)
    return _perifocal_to_radec(
        x_pf, y_pf, elements.argument_of_periapsis, elements.inclination, elements.longitude_ascending_node, t
    )


def _ra_rate_on_sky(ra1_deg: float, ra2_deg: float, dec_deg: float, dt_seconds: float) -> float:
    """On-sky RA rate in arcsec/sec, i.e. d(RA)/dt * cos(dec) -- matches JPL Horizons' RA_rate
    convention, and the ITrackingRate interface's "absolute rate on the sky" semantics."""
    dra = ra2_deg - ra1_deg
    if dra > 180:
        dra -= 360
    elif dra < -180:
        dra += 360
    return dra * 3600.0 * math.cos(math.radians(dec_deg)) / dt_seconds


class BaseTelescope(
    WeatherAwareMixin, MotionStatusMixin, WaitForMotionMixin, ITelescope, IFitsHeaderBefore, Module, metaclass=ABCMeta
):
    """Base class for telescopes."""

    __module__ = "pyobs.modules.telescope"

    def __init__(
        self,
        fits_headers: dict[str, Any] | None = None,
        min_altitude: float = 10,
        wait_for_dome: str | None = None,
        **kwargs: Any,
    ):
        """Initialize a new base telescope.

        Args:
            fits_headers: Additional FITS headers to send.
            min_altitude: Minimal altitude for telescope.
            wait_for_dome: Name of dome module to wait for.
        """
        Module.__init__(self, **kwargs)

        # store
        self._fits_headers = fits_headers if fits_headers is not None else {}
        self._min_altitude = min_altitude

        # some multi-threading stuff
        self._lock_moving = asyncio.Lock()
        self._abort_move = asyncio.Event()

        # celestial status
        self._celestial_headers: dict[str, Any] = {}

        # body/orbital-element tracking state (IPointingBody/IPointingOrbitalElements)
        self._tracked_body: str | None = None
        self._tracked_elements: OrbitalElements | None = None
        self._last_position_nudge: Time | None = None
        self._last_tracking_used_native_mode = False
        self._warned_slow_update_interval = False

        # add thread func
        self.add_background_task(self._celestial, True)
        self.add_background_task(self._track_refresh, True)

        # init mixins
        WeatherAwareMixin.__init__(self, **kwargs)
        MotionStatusMixin.__init__(self, **kwargs)
        WaitForMotionMixin.__init__(
            self,
            wait_for_modules=None if wait_for_dome is None else [wait_for_dome],
            wait_for_timeout=60000,
            wait_for_states=[MotionStatus.POSITIONED, MotionStatus.TRACKING],
        )

        # register exception
        self._register_exception(exc.MotionError, 3, timespan=600, callback=self._default_remote_error_callback)

    @property
    def _position_radec(self) -> tuple[float, float] | None:
        """Current RA/Dec position in degrees, or None if unknown. Override in subclasses."""
        return None

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # open mixins
        await WeatherAwareMixin.open(self)
        await MotionStatusMixin.open(self)

    @abstractmethod
    async def _move_radec(self, ra: float, dec: float, abort_event: asyncio.Event) -> None:
        """Actually starts tracking on given coordinates. Must be implemented by derived classes.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.
            abort_event: Event that gets triggered when movement should be aborted.

        Raises:
            MoveError: If telescope cannot be moved.
        """
        ...

    @timeout(1200)
    async def move_radec(self, ra: float, dec: float, **kwargs: Any) -> None:
        """Starts tracking on given coordinates.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.

        Raises:
            MoveError: If telescope cannot be moved.
        """

        # no RA/Dec telescope?
        if not isinstance(self, IPointingRaDec):
            raise NotImplementedError

        # do nothing, if initializing, parking or parked
        if self.motion_status() in [MotionStatus.INITIALIZING, MotionStatus.PARKING, MotionStatus.PARKED]:
            return

        # check observer
        if self.observer is None:
            raise ValueError("No observer given.")

        # to alt/az
        ra_dec = SkyCoord(ra * u.deg, dec * u.deg, frame=ICRS)
        alt_az = self.observer.altaz(Time.now(), ra_dec)

        # check altitude
        if alt_az.alt.degree < self._min_altitude:
            raise ValueError(
                f"Destination altitude below limit: alt={alt_az.alt.degree:.2f}° "
                f"az={alt_az.az.degree:.2f}° (min={self._min_altitude:.2f}°) for "
                f"ra={ra:.5f}° dec={dec:.5f}° at {Time.now().isot} from "
                f"lon={self.observer.location.lon.degree:.4f}° "
                f"lat={self.observer.location.lat.degree:.4f}° "
                f"height={self.observer.location.height.value:.1f}m."
            )

        # acquire lock
        async with LockWithAbort(self._lock_moving, self._abort_move):
            # log and event
            await self._change_motion_status(MotionStatus.SLEWING)
            log.info(
                "Moving telescope to RA=%s (%.5f°), Dec=%s (%.5f°)...",
                ra_dec.ra.to_string(sep=":", unit=u.hour, pad=True),
                ra,
                ra_dec.dec.to_string(sep=":", unit=u.deg, pad=True),
                dec,
            )
            await self.comm.send_event(MoveRaDecEvent(ra=ra, dec=dec))

            # a plain move_radec is "go to this fixed coordinate" -- stop any ongoing
            # body/orbital-element tracking and reset to native sidereal tracking, so a mount
            # left in e.g. lunar/custom-rate mode from a previous target doesn't silently keep
            # applying a stale rate to this new, unrelated sidereal target
            self._tracked_body = None
            self._tracked_elements = None
            if isinstance(self, ITrackingMode):
                await self.set_tracking_mode(TrackingMode.SIDEREAL)

            # track telescope
            await self._move_radec(ra, dec, abort_event=self._abort_move)
            log.info("Reached destination")

            # move dome, if exists
            await self._wait_for_motion(self._abort_move)

            # finish slewing
            await self._change_motion_status(MotionStatus.TRACKING)

            # update headers now
            asyncio.create_task(self._update_celestial_headers())
            log.info("Finished moving telescope.")

    @abstractmethod
    async def _move_altaz(self, alt: float, az: float, abort_event: asyncio.Event) -> None:
        """Actually moves to given coordinates. Must be implemented by derived classes.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.
            abort_event: Event that gets triggered when movement should be aborted.

        Raises:
            MoveError: If telescope cannot be moved.
        """
        ...

    @timeout(1200)
    async def move_altaz(self, alt: float, az: float, **kwargs: Any) -> None:
        """Moves to given coordinates.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.

        Raises:
            MoveError: If telescope cannot be moved.
        """

        # no Alt/Az telescope?
        if not isinstance(self, IPointingAltAz):
            raise NotImplementedError

        # do nothing, if initializing, parking or parked
        if self.motion_status() in [MotionStatus.INITIALIZING, MotionStatus.PARKING, MotionStatus.PARKED]:
            return

        # check altitude
        if alt < self._min_altitude:
            raise ValueError(
                f"Destination altitude below limit: alt={alt:.2f}° az={az:.2f}° "
                f"(min={self._min_altitude:.2f}°) at {Time.now().isot}."
            )

        # acquire lock
        async with LockWithAbort(self._lock_moving, self._abort_move):
            # log and event
            log.info("Moving telescope to Alt=%.2f°, Az=%.2f°...", alt, az)
            await self.comm.send_event(MoveAltAzEvent(alt=alt, az=az))
            await self._change_motion_status(MotionStatus.SLEWING)

            # holding a fixed alt/az is incompatible with continued body/orbital-element
            # tracking or sidereal/lunar/solar motion -- stop both, same reasoning as move_radec
            self._tracked_body = None
            self._tracked_elements = None
            if isinstance(self, ITrackingMode):
                await self.set_tracking_mode(TrackingMode.OFF)

            # move telescope
            await self._move_altaz(alt, az, abort_event=self._abort_move)
            log.info("Reached destination")

            # move dome, if exists
            await self._wait_for_motion(self._abort_move)

            # finish slewing
            await self._change_motion_status(MotionStatus.POSITIONED)

            # update headers now
            asyncio.create_task(self._update_celestial_headers())
            log.info("Finished moving telescope.")

    @abstractmethod
    async def _set_tracking_rate(self, ra_rate: float, dec_rate: float) -> None:
        """Actually applies an absolute tracking rate to hardware. Must be implemented by
        derived classes that support ITrackingRate.

        Args:
            ra_rate: Rate in RA, arcsec/sec on the sky.
            dec_rate: Rate in Dec, arcsec/sec on the sky.

        Raises:
            MoveError: If rate could not be set.
        """
        ...

    async def set_tracking_rate(self, ra_rate: float, dec_rate: float, **kwargs: Any) -> None:
        """Public entry point for external/manual callers. Enforces the SIDEREAL precondition:
        a continuous rate is only ever meaningful as a small correction on top of sidereal
        motion, never on top of OFF -- see design doc's "Required base mode" section.

        Args:
            ra_rate: Rate in RA, arcsec/sec on the sky.
            dec_rate: Rate in Dec, arcsec/sec on the sky.

        Raises:
            MoveError: If rate could not be set.
        """
        if isinstance(self, ITrackingMode):
            current = self.comm.get_own_state(ITrackingMode)
            if current is None or current.mode != TrackingMode.SIDEREAL:
                await self.set_tracking_mode(TrackingMode.SIDEREAL)
        await self._set_tracking_rate(ra_rate, dec_rate)
        await self.comm.set_state(ITrackingRate, TrackingRateState(ra_rate=ra_rate, dec_rate=dec_rate))

    async def _resolve_body_with_rate(self, body: str, t: Time | None = None) -> tuple[float, float, float, float]:
        """Resolves a body name to (ra, dec, ra_rate, dec_rate) -- degrees and arcsec/sec on the sky.

        Resolution chain:
            1. astropy.coordinates.get_body -- Sun, Moon, major planets. No rate output, so
               finite-differenced locally (cheap: no network call).
            2. JPL Horizons fallback -- anything not covered above. Horizons' ephemerides table
               already includes RA_rate/DEC_rate columns alongside position for the same query,
               so no separate query or finite-differencing is needed.

        Raises:
            ValueError: If body name is not resolvable.
        """
        now = t if t is not None else Time.now()
        location = self.observer.location if self._observer is not None else None

        try:
            c1 = get_body(body, now, location=location)
            c2 = get_body(body, now + 1 * u.s, location=location)
        except KeyError:
            pass
        else:
            ra, dec = float(c1.icrs.ra.degree), float(c1.icrs.dec.degree)
            ra_rate = _ra_rate_on_sky(ra, float(c2.icrs.ra.degree), dec, 1.0)
            dec_rate = (float(c2.icrs.dec.degree) - dec) * 3600.0
            return ra, dec, ra_rate, dec_rate

        loop = asyncio.get_event_loop()

        def _query() -> tuple[float, float, float, float]:
            loc = None
            if self._observer is not None:
                site = self.observer.location
                loc = {
                    "lon": float(site.lon.degree),
                    "lat": float(site.lat.degree),
                    "elevation": float(site.height.to(u.km).value),
                }
            horizons = Horizons(id=body, location=loc, epochs=now.jd)
            eph = horizons.ephemerides()
            return (
                float(eph["RA"][0]),
                float(eph["DEC"][0]),
                float(eph["RA_rate"][0]) / 3600.0,
                float(eph["DEC_rate"][0]) / 3600.0,
            )

        try:
            return await loop.run_in_executor(None, _query)
        except Exception as e:
            raise ValueError(f"Could not resolve body '{body}'.") from e

    async def _resolve_body(self, body: str) -> tuple[float, float]:
        """Resolves a body name to (ra, dec) in degrees, ICRS.

        Raises:
            ValueError: If body name is not resolvable.
        """
        ra, dec, _, _ = await self._resolve_body_with_rate(body)
        return ra, dec

    async def track_body(self, body: str, **kwargs: Any) -> None:
        """Starts tracking a named solar-system body.

        Args:
            body: Name resolvable to an ephemeris (e.g. 'moon', 'mars', 'jupiter', or an
                  asteroid/comet designation known to JPL Horizons).

        Raises:
            MoveError: If telescope could not be moved.
            ValueError: If body name is not resolvable.
        """
        if not isinstance(self, IPointingBody):
            raise NotImplementedError
        ra, dec = await self._resolve_body(body)
        await self.move_radec(ra, dec)
        self._tracked_body = body
        self._tracked_elements = None
        self._last_position_nudge = Time.now()
        self._warned_slow_update_interval = False
        await self._track_refresh_tick()

    async def track_orbital_elements(self, elements: OrbitalElements, **kwargs: Any) -> None:
        """Starts tracking a body defined by orbital elements.

        Args:
            elements: Orbital elements of the body to track.

        Raises:
            MoveError: If telescope could not be moved.
            ValueError: If elements are incomplete (neither mean_anomaly nor perihelion_time given).
        """
        if not isinstance(self, IPointingOrbitalElements):
            raise NotImplementedError
        if elements.mean_anomaly is None and elements.perihelion_time is None:
            raise ValueError("OrbitalElements must set either mean_anomaly or perihelion_time.")
        ra, dec = _propagate_elements(elements, Time.now())
        await self.move_radec(ra, dec)
        self._tracked_elements = elements
        self._tracked_body = None
        self._last_position_nudge = Time.now()
        self._warned_slow_update_interval = False
        await self._track_refresh_tick()

    def _native_tracking_mode_for_body(self, body: str) -> TrackingMode | None:
        """Which discrete TrackingMode a body should ideally use, if the driver has it.
        Nothing beyond Sun/Moon -- there's no TrackingMode.PLANET/ASTEROID; everything else
        always goes through ITrackingRate."""
        name = body.strip().lower()
        if name == "moon":
            return TrackingMode.LUNAR
        if name == "sun":
            return TrackingMode.SOLAR
        return None

    async def _dispatch_tracking(self, mode: TrackingMode | None, ra_rate: float, dec_rate: float) -> bool:
        """Applies a computed tracking rate to hardware: native mode if available and applicable
        (Sun/Moon on a driver that has that mode), else a continuous rate via ITrackingRate.

        Returns:
            True if native TrackingMode dispatch was used (rate not applied), False if
            ITrackingRate dispatch was used.

        Raises:
            MoveError: If hardware supports neither a matching native mode nor ITrackingRate.
        """
        if mode is not None and isinstance(self, ITrackingMode):
            current = self.comm.get_own_state(ITrackingMode)
            try:
                if current is None or current.mode != mode:
                    await self.set_tracking_mode(mode)
                return True
            except ValueError:
                pass  # hardware doesn't support this native mode -- fall through to rate

        if isinstance(self, ITrackingRate):
            await self._set_tracking_rate(ra_rate, dec_rate)
            await self.comm.set_state(ITrackingRate, TrackingRateState(ra_rate=ra_rate, dec_rate=dec_rate))
            return False

        raise exc.MoveError(f"Cannot track: hardware supports neither native mode {mode} nor an arbitrary rate.")

    async def _track_refresh_tick(self) -> None:
        """Single refresh cycle: recomputes position/rate for whatever's being tracked and
        applies it. Shared by the background task and by track_body/track_orbital_elements'
        initial call, so the mount doesn't sit in the just-reset default (sidereal/off) for a
        whole refresh interval right after the initial slew."""
        if self._tracked_body is None and self._tracked_elements is None:
            return
        if self._lock_moving.locked():
            # a slew is in progress -- nothing should be actively rate-tracking right now; the
            # resync nudge after the slew completes absorbs whatever gap this tick skipped
            return

        async with LockWithAbort(self._lock_moving, self._abort_move):
            try:
                now = Time.now()
                mode = None
                if self._tracked_body is not None:
                    ra, dec, ra_rate, dec_rate = await self._resolve_body_with_rate(self._tracked_body, now)
                    mode = self._native_tracking_mode_for_body(self._tracked_body)
                else:
                    assert self._tracked_elements is not None
                    ra, dec = _propagate_elements(self._tracked_elements, now)
                    ra2, dec2 = _propagate_elements(self._tracked_elements, now + 1 * u.s)
                    ra_rate = _ra_rate_on_sky(ra, ra2, dec, 1.0)
                    dec_rate = (dec2 - dec) * 3600.0

                used_native_mode = await self._dispatch_tracking(mode, ra_rate, dec_rate)
                self._last_tracking_used_native_mode = used_native_mode

                # periodic drift-correction reslew -- bypasses the public move_radec (which
                # would reset tracking mode and clear the very state this tick is maintaining),
                # calling the hardware hook directly instead
                due = (
                    self._last_position_nudge is None
                    or (now - self._last_position_nudge).sec >= _POSITION_NUDGE_INTERVAL_SECONDS
                )
                if due and not used_native_mode:
                    await self._move_radec(ra, dec, abort_event=self._abort_move)
                    self._last_position_nudge = now
            except Exception:
                log.exception("Error refreshing body/orbital-element tracking.")

    def _tracking_refresh_interval(self) -> float:
        """Accuracy-driven refresh interval for the currently-tracked body/elements, clamped
        against this driver's own TrackingRateCapabilities.min_update_interval if published. The
        Moon needs a much tighter interval than planets/asteroids, but only when actually falling
        back to ITrackingRate for it (no native TrackingMode.LUNAR available) -- see design doc's
        "Recompute cadence" section. Reflects the outcome of the most recent dispatch rather than
        re-deriving it, since only that tick's actual result (including capability rejection via
        ValueError) is authoritative.
        """
        if (
            self._tracked_body is not None
            and self._tracked_body.strip().lower() == "moon"
            and not self._last_tracking_used_native_mode
        ):
            accuracy_driven_interval = _MOON_FALLBACK_REFRESH_INTERVAL_SECONDS
        else:
            accuracy_driven_interval = _DEFAULT_REFRESH_INTERVAL_SECONDS

        if not isinstance(self, ITrackingRate):
            return accuracy_driven_interval
        capabilities = self.comm.get_own_capabilities(ITrackingRate)
        if capabilities is None:
            return accuracy_driven_interval

        if capabilities.min_update_interval > accuracy_driven_interval and not self._warned_slow_update_interval:
            log.warning(
                "This mount's minimum tracking-rate update interval (%.1fs) is coarser than what "
                "the current target's accuracy needs (%.1fs) -- tracking will be degraded.",
                capabilities.min_update_interval,
                accuracy_driven_interval,
            )
            self._warned_slow_update_interval = True

        return max(accuracy_driven_interval, capabilities.min_update_interval)

    async def _track_refresh(self) -> None:
        """Background task: refreshes rate/position for body/orbital-element tracking while
        one is active; sleeps between ticks otherwise."""
        await asyncio.sleep(10)
        while True:
            if self._tracked_body is None and self._tracked_elements is None:
                await asyncio.sleep(5)
                continue

            await self._track_refresh_tick()
            await asyncio.sleep(self._tracking_refresh_interval())

    async def get_fits_header_before(
        self, namespaces: list[str] | None = None, **kwargs: Any
    ) -> dict[str, FitsHeaderEntry]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # define base header
        hdr: dict[str, FitsHeaderEntry] = {}

        # positions
        coords_ra_dec = None
        if isinstance(self, IPointingRaDec) and self._position_radec is not None:
            ra, dec = self._position_radec
            coords_ra_dec = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame=ICRS)
        coords_alt_az = None
        if isinstance(self, IPointingAltAz) and coords_ra_dec is not None and self._observer is not None:
            coords_alt_az = self.observer.altaz(Time.now(), coords_ra_dec)

        # set coordinate headers
        if coords_ra_dec is not None:
            hdr["TEL-RA"] = FitsHeaderEntry(float(coords_ra_dec.ra.degree), "Right ascension of telescope [degrees]")
            hdr["TEL-DEC"] = FitsHeaderEntry(float(coords_ra_dec.dec.degree), "Declination of telescope [degrees]")
        if coords_alt_az is not None:
            hdr["TEL-ALT"] = FitsHeaderEntry(float(coords_alt_az.alt.degree), "Telescope altitude [degrees]")
            hdr["TEL-AZ"] = FitsHeaderEntry(float(coords_alt_az.az.degree), "Telescope azimuth [degrees]")
            hdr["TEL-ZD"] = FitsHeaderEntry(
                90.0 - float(coords_alt_az.alt.degree), "Telescope zenith distance [degrees]"
            )
            hdr["AIRMASS"] = FitsHeaderEntry(float(coords_alt_az.secz.value), "Airmass of observation start")

        # convert to sexagesimal
        if coords_ra_dec is not None:
            hdr["RA"] = FitsHeaderEntry(
                str(coords_ra_dec.ra.to_string(sep=":", unit=u.hour, pad=True)), "Right ascension of object"
            )
            hdr["DEC"] = FitsHeaderEntry(
                str(coords_ra_dec.dec.to_string(sep=":", unit=u.deg, pad=True)), "Declination of object"
            )

        # site location
        if self._observer is not None:
            hdr["LATITUDE"] = FitsHeaderEntry(float(self.observer.location.lat.degree), "Latitude of telescope [deg N]")
            hdr["LONGITUD"] = FitsHeaderEntry(
                float(self.observer.location.lon.degree), "Longitude of telescope [deg E]"
            )
            hdr["HEIGHT"] = FitsHeaderEntry(float(self.observer.location.height.value), "Altitude of telescope [m]")

        # add static fits headers
        for key, value in self._fits_headers.items():
            hdr[key] = FitsHeaderEntry(value[0], value[1])

        # add celestial headers
        for key, value in self._celestial_headers.items():
            hdr[key] = FitsHeaderEntry(value[0], value[1])

        # finish
        return hdr

    async def _celestial(self) -> None:
        """Thread for continuously calculating positions and distances to celestial objects like moon and sun."""

        # wait a little
        await asyncio.sleep(10)

        # run until closing
        while True:
            # update headers
            try:
                await self._update_celestial_headers()
            except Exception:
                log.exception("Something went wrong.")

            # sleep a little
            await asyncio.sleep(30)

    async def _update_celestial_headers(self) -> None:
        """Calculate positions and distances to celestial objects like moon and sun."""
        # get now
        now = Time.now()

        # no observer?
        if self._observer is None:
            return

        # get telescope alt/az
        tel_altaz = None
        if isinstance(self, IPointingAltAz) and self._position_radec is not None:
            radec = SkyCoord(ra=self._position_radec[0] * u.deg, dec=self._position_radec[1] * u.deg, frame=ICRS)
            tel_altaz = self.observer.altaz(now, radec)

            # publish alt/az state
            if self._comm is not None:
                await self.comm.set_state(
                    IPointingAltAz,
                    AltAzState(alt=float(tel_altaz.alt.degree), az=float(tel_altaz.az.degree)),
                )

        # get current moon and sun information
        moon_altaz = self.observer.moon_altaz(now)
        moon_frac = self.observer.moon_illumination(now)
        sun_altaz = self.observer.sun_altaz(now)

        # store it
        self._celestial_headers = {
            "MOONALT": (float(moon_altaz.alt.degree), "Lunar altitude"),
            "MOONFRAC": (float(moon_frac), "Fraction of the moon illuminated"),
            "SUNALT": (float(sun_altaz.alt.degree), "Solar altitude"),
        }

        # calculate distance to telescope
        if tel_altaz is not None:
            moon_dist = tel_altaz.separation(moon_altaz) if tel_altaz is not None else None
            sun_dist = tel_altaz.separation(sun_altaz) if tel_altaz is not None else None
            self._celestial_headers["MOONDIST"] = (
                None if moon_dist is None else float(moon_dist.degree),
                "Lunar distance from target",
            )
            self._celestial_headers["SUNDIST"] = (
                None if sun_dist is None else float(sun_dist.degree),
                "Solar Distance from Target",
            )

    def _calculate_derotator_position(self, ra: float, dec: float, alt: float, obstime: Time) -> float:
        target = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="gcrs")
        if self._observer is None:
            raise ValueError("No observer.")
        parallactic = self.observer.parallactic_angle(time=obstime, target=target).deg
        return float(parallactic - alt)


__all__ = ["BaseTelescope"]
