import asyncio
from abc import ABCMeta, abstractmethod
from typing import Dict, Any, Tuple, Union, List, Optional
from astropy.coordinates import SkyCoord, ICRS, AltAz
import astropy.units as u
import logging

from pyobs.events import MoveRaDecEvent, MoveAltAzEvent
from pyobs.interfaces import ITelescope, IFitsHeaderBefore
from pyobs.modules import Module
from pyobs.mixins import MotionStatusMixin, WeatherAwareMixin, WaitForMotionMixin
from pyobs.modules import timeout
from pyobs.utils.enums import MotionStatus
from pyobs.utils.threads import LockWithAbort
from pyobs.utils.time import Time
from pyobs.utils import exceptions as exc

log = logging.getLogger(__name__)


class BaseTelescope(
    WeatherAwareMixin, MotionStatusMixin, WaitForMotionMixin, ITelescope, IFitsHeaderBefore, Module, metaclass=ABCMeta
):
    """Base class for telescopes."""

    __module__ = "pyobs.modules.telescope"

    def __init__(
        self,
        fits_headers: Optional[Dict[str, Any]] = None,
        min_altitude: float = 10,
        wait_for_dome: Optional[str] = None,
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
        self._celestial_headers: Dict[str, Any] = {}

        # add thread func
        self.add_background_task(self._celestial, True)

        # init mixins
        WeatherAwareMixin.__init__(self, **kwargs)
        MotionStatusMixin.__init__(self, **kwargs)
        WaitForMotionMixin.__init__(
            self,
            wait_for_modules=None if wait_for_dome is None else [wait_for_dome],
            wait_for_timeout=60000,
            wait_for_states=[MotionStatus.POSITIONED, MotionStatus.TRACKING],
        )

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
            CannotMoveException: If telescope cannot be moved.
            ConfigError: If anything is wrong with the config.
            CoordinateError: If coordinates are invalid.
        """
        ...

    @timeout(1200)
    async def move_radec(self, ra: float, dec: float, **kwargs: Any) -> None:
        """Starts tracking on given coordinates.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.

        Raises:
            CannotMoveException: If telescope cannot be moved.
            ConfigError: If anything is wrong with the config.
            CoordinateError: If coordinates are invalid.
        """

        # do nothing, if initializing, parking or parked
        if await self.get_motion_status() in [MotionStatus.INITIALIZING, MotionStatus.PARKING, MotionStatus.PARKED]:
            return

        # check observer
        if self.observer is None:
            raise exc.ConfigError("No observer given.")

        # to alt/az
        ra_dec = SkyCoord(ra * u.deg, dec * u.deg, frame=ICRS)
        alt_az = self.observer.altaz(Time.now(), ra_dec)

        # check altitude
        if alt_az.alt.degree < self._min_altitude:
            raise exc.CoordinateError("Destination altitude below limit.")

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
            CannotMoveException: If telescope cannot be moved.
            ConfigError: If anything is wrong with the config.
            CoordinateError: If coordinates are invalid.
        """
        ...

    @timeout(1200)
    async def move_altaz(self, alt: float, az: float, **kwargs: Any) -> None:
        """Moves to given coordinates.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.

        Raises:
            CannotMoveException: If telescope cannot be moved.
            ConfigError: If anything is wrong with the config.
            CoordinateError: If coordinates are invalid.
        """

        # do nothing, if initializing, parking or parked
        if await self.get_motion_status() in [MotionStatus.INITIALIZING, MotionStatus.PARKING, MotionStatus.PARKED]:
            return

        # check altitude
        if alt < self._min_altitude:
            raise exc.CoordinateError("Destination altitude below limit.")

        # acquire lock
        async with LockWithAbort(self._lock_moving, self._abort_move):
            # log and event
            log.info("Moving telescope to Alt=%.2f°, Az=%.2f°...", alt, az)
            await self.comm.send_event(MoveAltAzEvent(alt=alt, az=az))
            await self._change_motion_status(MotionStatus.SLEWING)

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

    async def get_fits_header_before(
        self, namespaces: Optional[List[str]] = None, **kwargs: Any
    ) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # define base header
        hdr: Dict[str, Union[Any, Tuple[Any, str]]] = {}

        # positions
        try:
            ra, dec = await self.get_radec()
            coords_ra_dec = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame=ICRS)
            alt, az = await self.get_altaz()
            coords_alt_az = SkyCoord(alt=alt * u.deg, az=az * u.deg, frame=AltAz)

        except Exception as e:
            log.warning("Could not fetch telescope position: %s", e)
            coords_ra_dec, coords_alt_az = None, None

        # set coordinate headers
        if coords_ra_dec is not None:
            hdr["TEL-RA"] = (float(coords_ra_dec.ra.degree), "Right ascension of telescope [degrees]")
            hdr["TEL-DEC"] = (float(coords_ra_dec.dec.degree), "Declination of telescope [degrees]")
        if coords_alt_az is not None:
            hdr["TEL-ALT"] = (float(coords_alt_az.alt.degree), "Telescope altitude [degrees]")
            hdr["TEL-AZ"] = (float(coords_alt_az.az.degree), "Telescope azimuth [degrees]")
            hdr["TEL-ZD"] = (90.0 - hdr["TEL-ALT"][0], "Telescope zenith distance [degrees]")
            hdr["AIRMASS"] = (float(coords_alt_az.secz.value), "Airmass of observation start")

        # convert to sexagesimal
        if coords_ra_dec is not None:
            hdr["RA"] = (str(coords_ra_dec.ra.to_string(sep=":", unit=u.hour, pad=True)), "Right ascension of object")
            hdr["DEC"] = (str(coords_ra_dec.dec.to_string(sep=":", unit=u.deg, pad=True)), "Declination of object")

        # site location
        if self.observer is not None:
            hdr["LATITUDE"] = (float(self.observer.location.lat.degree), "Latitude of telescope [deg N]")
            hdr["LONGITUD"] = (float(self.observer.location.lon.degree), "Longitude of telescope [deg E]")
            hdr["HEIGHT"] = (float(self.observer.location.height.value), "Altitude of telescope [m]")

        # add static fits headers
        for key, value in self._fits_headers.items():
            hdr[key] = tuple(value)

        # add celestial headers
        for key, value in self._celestial_headers.items():
            hdr[key] = tuple(value)

        # finish
        return hdr

    async def _celestial(self) -> None:
        """Thread for continuously calculating positions and distances to celestial objects like moon and sun."""

        # wait a little
        await asyncio.sleep(10)

        # run until closing
        while True:
            # update headers
            await self._update_celestial_headers()

            # sleep a little
            await asyncio.sleep(30)

    async def _update_celestial_headers(self) -> None:
        """Calculate positions and distances to celestial objects like moon and sun."""
        # get now
        now = Time.now()
        alt: Optional[float]
        az: Optional[float]

        # no observer?
        if self.observer is None:
            return

        # get telescope alt/az
        try:
            alt, az = await self.get_altaz()
            tel_altaz = SkyCoord(alt=alt * u.deg, az=az * u.deg, frame="altaz")
        except:
            alt, az, tel_altaz = None, None, None

        # get current moon and sun information
        moon_altaz = self.observer.moon_altaz(now)
        moon_frac = self.observer.moon_illumination(now)
        sun_altaz = self.observer.sun_altaz(now)

        # calculate distance to telescope
        moon_dist = tel_altaz.separation(moon_altaz) if tel_altaz is not None else None
        sun_dist = tel_altaz.separation(sun_altaz) if tel_altaz is not None else None

        # store it
        self._celestial_headers = {
            "MOONALT": (float(moon_altaz.alt.degree), "Lunar altitude"),
            "MOONFRAC": (float(moon_frac), "Fraction of the moon illuminated"),
            "MOONDIST": (None if moon_dist is None else float(moon_dist.degree), "Lunar distance from target"),
            "SUNALT": (float(sun_altaz.alt.degree), "Solar altitude"),
            "SUNDIST": (None if sun_dist is None else float(sun_dist.degree), "Solar Distance from Target"),
        }


__all__ = ["BaseTelescope"]
