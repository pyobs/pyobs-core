from __future__ import annotations

import asyncio
from typing import Any, Literal

import astropy.units as u
import numpy as np
from astropy import constants
from astropy.coordinates import SkyCoord, get_sun

from pyobs.interfaces import (
    HeliocentricPolarState,
    HeliographicStonyhurstState,
    HelioprojectiveState,
    IPointingHeliocentricPolar,
    IPointingHeliographicStonyhurst,
    IPointingHelioprojective,
    IPointingRaDec,
    RaDecState,
    TrackingMode,
)
from pyobs.modules.telescope._dummytelescopebase import _DummyTelescopeBase
from pyobs.modules.telescope.basetelescope import BaseTelescope
from pyobs.utils.threads import LockWithAbort
from pyobs.utils.time import Time


class DummySolarTelescope(
    _DummyTelescopeBase, IPointingHeliocentricPolar, IPointingHeliographicStonyhurst, IPointingHelioprojective
):
    """A dummy telescope dedicated to solar pointing (Heliocentric Polar/Heliographic Stonyhurst/
    Helioprojective), for testing -- it always tracks the Sun and does not support arbitrary
    body/orbital-element tracking (see dummy-telescope-split-design.md).
    """

    __module__ = "pyobs.modules.telescope"

    _SOLAR_FOLLOW_INTERVAL_SECONDS = 10.0

    def __init__(self, **kwargs: Any):
        _DummyTelescopeBase.__init__(self, **kwargs)

        # (kind, a, b) of the last move_heliocentric_polar/move_heliographic_stonyhurst/
        # move_helioprojective call, or None if not currently following a solar-relative target.
        # Re-resolved to RA/Dec every tick by _solar_follow_task since the Sun moves across the sky
        # (and, for heliocentric-polar/heliographic-stonyhurst targets fixed on the rotating solar
        # surface, also rotates).
        self._solar_target: (
            tuple[Literal["heliocentric_polar", "heliographic_stonyhurst", "helioprojective"], float, float] | None
        ) = None

        self.add_background_task(self._solar_follow_task)

    async def open(self) -> None:
        """Open module."""
        await _DummyTelescopeBase.open(self)

        # no solar target is being followed yet -- publish the disk centre as a placeholder so
        # the pubsub nodes exist (real values get set once a move_heliocentric_polar/
        # move_heliographic_stonyhurst/move_helioprojective call comes in)
        await self.comm.set_state(IPointingHeliocentricPolar, HeliocentricPolarState(mu=1.0, psi=0.0))
        await self.comm.set_state(IPointingHeliographicStonyhurst, HeliographicStonyhurstState(lon=0.0, lat=0.0))
        await self.comm.set_state(IPointingHelioprojective, HelioprojectiveState(theta_x=0.0, theta_y=0.0))

    @staticmethod
    def _heliocentric_polar_to_radec(mu: float, psi: float, time: Time) -> tuple[float, float]:
        """Converts Heliocentric Polar (mu, psi) to (ra, dec) in degrees, ICRS. Mirrors
        HeliocentricPolarTarget.coordinates() (pyobs/robotic/scheduler/targets), except psi is
        taken in degrees here (matching IPointingHeliocentricPolar's declared unit) rather than
        implicitly in radians."""
        from sunpy.coordinates import Helioprojective

        alpha = np.arccos(mu)
        d_sun = get_sun(time).distance
        r_sun = constants.R_sun  # type: ignore[missing-attribute]
        theta = np.arctan(r_sun * np.sin(alpha) / (d_sun - (r_sun * mu)))
        psi_rad = np.radians(psi)
        tx = -theta * np.sin(psi_rad)
        ty = theta * np.cos(psi_rad)
        coord = SkyCoord(tx, ty, obstime=time, frame=Helioprojective, observer="earth")
        icrs = coord.icrs
        return float(icrs.ra.degree), float(icrs.dec.degree)

    @staticmethod
    def _heliographic_stonyhurst_to_radec(lon: float, lat: float, time: Time) -> tuple[float, float]:
        """Converts Heliographic Stonyhurst (lon, lat), in degrees, to (ra, dec) in degrees, ICRS."""
        from sunpy.coordinates import HeliographicStonyhurst

        coord = SkyCoord(lon * u.deg, lat * u.deg, frame=HeliographicStonyhurst, obstime=time, observer="earth")
        icrs = coord.transform_to("icrs")
        return float(icrs.ra.degree), float(icrs.dec.degree)

    @staticmethod
    def _helioprojective_to_radec(theta_x: float, theta_y: float, time: Time) -> tuple[float, float]:
        """Converts Helioprojective (theta_x, theta_y), in degrees, to (ra, dec) in degrees, ICRS."""
        from sunpy.coordinates import Helioprojective

        coord = SkyCoord(theta_x * u.deg, theta_y * u.deg, obstime=time, frame=Helioprojective, observer="earth")
        icrs = coord.icrs
        return float(icrs.ra.degree), float(icrs.dec.degree)

    async def move_radec(self, ra: float, dec: float, **kwargs: Any) -> None:
        # a plain move_radec/move_altaz is "go to this fixed coordinate" -- not "follow the Sun
        # at this Sun-relative offset" anymore, so stop following, same reasoning as
        # BaseTelescope.move_radec clearing _tracked_body/_tracked_elements.
        self._solar_target = None
        await BaseTelescope.move_radec(self, ra, dec, **kwargs)

    async def move_altaz(self, alt: float, az: float, **kwargs: Any) -> None:
        self._solar_target = None
        await BaseTelescope.move_altaz(self, alt, az, **kwargs)

    async def move_heliocentric_polar(self, mu: float, psi: float, **kwargs: Any) -> None:
        """Moves to and continuously tracks a Heliocentric Polar (mu, psi) coordinate."""
        ra, dec = self._heliocentric_polar_to_radec(mu, psi, Time.now())
        await self.move_radec(ra, dec)
        self._solar_target = ("heliocentric_polar", mu, psi)
        await self.set_tracking_mode(TrackingMode.SOLAR)
        await self.comm.set_state(IPointingHeliocentricPolar, HeliocentricPolarState(mu=mu, psi=psi))

    async def move_heliographic_stonyhurst(self, lon: float, lat: float, **kwargs: Any) -> None:
        """Moves to and continuously tracks a Heliographic Stonyhurst (lon, lat) coordinate."""
        ra, dec = self._heliographic_stonyhurst_to_radec(lon, lat, Time.now())
        await self.move_radec(ra, dec)
        self._solar_target = ("heliographic_stonyhurst", lon, lat)
        await self.set_tracking_mode(TrackingMode.SOLAR)
        await self.comm.set_state(IPointingHeliographicStonyhurst, HeliographicStonyhurstState(lon=lon, lat=lat))

    async def move_helioprojective(self, theta_x: float, theta_y: float, **kwargs: Any) -> None:
        """Moves to and continuously tracks a Helioprojective (theta_x, theta_y) coordinate."""
        ra, dec = self._helioprojective_to_radec(theta_x, theta_y, Time.now())
        await self.move_radec(ra, dec)
        self._solar_target = ("helioprojective", theta_x, theta_y)
        await self.set_tracking_mode(TrackingMode.SOLAR)
        await self.comm.set_state(IPointingHelioprojective, HelioprojectiveState(theta_x=theta_x, theta_y=theta_y))

    async def _solar_follow_task(self) -> None:
        """Background task: while a solar-relative target is active, keeps the simulated
        position on it as the Sun moves across the sky (and, for heliocentric-polar/heliographic-
        stonyhurst targets, rotates) -- see dummy-telescope-split-design.md. Dummy-only: real solar
        hardware tracks the Sun natively, so there's no equivalent generic machinery in
        BaseTelescope."""
        while True:
            if self._solar_target is not None and not self._lock_moving.locked():
                async with LockWithAbort(self._lock_moving, self._abort_move):
                    kind, a, b = self._solar_target
                    now = Time.now()
                    if kind == "heliocentric_polar":
                        ra, dec = self._heliocentric_polar_to_radec(a, b, now)
                    elif kind == "heliographic_stonyhurst":
                        ra, dec = self._heliographic_stonyhurst_to_radec(a, b, now)
                    else:
                        ra, dec = self._helioprojective_to_radec(a, b, now)
                    self._position = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
                    await self.comm.set_state(IPointingRaDec, RaDecState(ra=ra, dec=dec))
                    await self._publish_altaz()

            await asyncio.sleep(self._SOLAR_FOLLOW_INTERVAL_SECONDS)


__all__ = ["DummySolarTelescope"]
