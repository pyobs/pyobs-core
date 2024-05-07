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
        exc.register_exception(exc.MotionError, 3, timespan=600, callback=self._default_remote_error_callback)

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

    @timeout(1200)
    async def move_radec(self, ra: float, dec: float, **kwargs: Any) -> None:
        """Starts tracking on given coordinates.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.

        Raises:
            MoveError: If telescope cannot be moved.
        """

        # do nothing, if initializing, parking or parked
        if await self.get_motion_status() in [MotionStatus.INITIALIZING, MotionStatus.PARKING, MotionStatus.PARKED]:
            return

        # check observer
        if self.observer is None:
            raise ValueError("No observer given.")

        # to alt/az
        ra_dec = SkyCoord(ra * u.deg, dec * u.deg, frame=ICRS)
        alt_az = self.observer.altaz(Time.now(), ra_dec)

        # check altitude
        if alt_az.alt.degree < self._min_altitude:
            raise ValueError("Destination altitude below limit.")

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
            await asyncio.create_task(self._calc_celestial_headers())
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

    @timeout(1200)
    async def move_altaz(self, alt: float, az: float, **kwargs: Any) -> None:
        """Moves to given coordinates.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.

        Raises:
            MoveError: If telescope cannot be moved.
        """

        # do nothing, if initializing, parking or parked
        if await self.get_motion_status() in [MotionStatus.INITIALIZING, MotionStatus.PARKING, MotionStatus.PARKED]:
            return

        # check altitude
        if alt < self._min_altitude:
            raise ValueError("Destination altitude below limit.")

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

            await asyncio.create_task(self._calc_celestial_headers())     #
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

        await self._add_coordinate_header(hdr)
        await self._add_side_information_header(hdr)

        self._copy_header(self._fits_headers, hdr)

        celestial_headers = await self._calc_celestial_headers()
        self._copy_header(celestial_headers, hdr)

        return hdr

    async def _add_coordinate_header(self, header: Dict[str, Union[Any, Tuple[Any, str]]]) -> None:
        try:
            ra, dec = await self.get_radec()
            coords_ra_dec = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame=ICRS)
            alt, az = await self.get_altaz()
            coords_alt_az = SkyCoord(alt=alt * u.deg, az=az * u.deg, frame=AltAz)
        except Exception as e:
            log.warning("Could not fetch telescope position: %s", e)
            return

        header["TEL-RA"] = (float(coords_ra_dec.ra.degree), "Right ascension of telescope [degrees]")
        header["TEL-DEC"] = (float(coords_ra_dec.dec.degree), "Declination of telescope [degrees]")

        header["TEL-ALT"] = (float(coords_alt_az.alt.degree), "Telescope altitude [degrees]")
        header["TEL-AZ"] = (float(coords_alt_az.az.degree), "Telescope azimuth [degrees]")
        header["TEL-ZD"] = (90.0 - header["TEL-ALT"][0], "Telescope zenith distance [degrees]")
        header["AIRMASS"] = (float(coords_alt_az.secz.value), "Airmass of observation start")

        header["RA"] = (str(coords_ra_dec.ra.to_string(sep=":", unit=u.hour, pad=True)), "Right ascension of object")
        header["DEC"] = (str(coords_ra_dec.dec.to_string(sep=":", unit=u.deg, pad=True)), "Declination of object")

    async def _add_side_information_header(self, header: Dict[str, Union[Any, Tuple[Any, str]]]) -> None:
        if self.observer is None:
            return

        header["LATITUDE"] = (float(self.observer.location.lat.degree), "Latitude of telescope [deg N]")
        header["LONGITUD"] = (float(self.observer.location.lon.degree), "Longitude of telescope [deg E]")
        header["HEIGHT"] = (float(self.observer.location.height.value), "Altitude of telescope [m]")

    @staticmethod
    def _copy_header(source: Dict[str, Any], target: Dict[str, Union[Any, Tuple[Any, str]]]) -> None:
        for key, value in source.items():
            target[key] = tuple(value)

    async def _calc_celestial_headers(self) -> Dict[str, Tuple[Optional[float], str]]:
        """Calculate positions and distances to celestial objects like moon and sun."""
        # get now
        now = Time.now()

        # no observer?
        if self.observer is None:
            return {}

        tel_altaz: Optional[SkyCoord] = None
        try:
            alt, az = await self.get_altaz()
            tel_altaz = SkyCoord(alt=alt * u.deg, az=az * u.deg, frame="altaz")
        except:
            pass

        # get current moon and sun information
        moon_altaz = self.observer.moon_altaz(now)
        moon_frac = self.observer.moon_illumination(now)
        sun_altaz = self.observer.sun_altaz(now)

        # calculate distance to telescope
        moon_dist = tel_altaz.separation(moon_altaz) if tel_altaz is not None else None
        sun_dist = tel_altaz.separation(sun_altaz) if tel_altaz is not None else None

        # store it
        celestial_headers = {
            "MOONALT": (float(moon_altaz.alt.degree), "Lunar altitude"),
            "MOONFRAC": (float(moon_frac), "Fraction of the moon illuminated"),
            "MOONDIST": (None if moon_dist is None else float(moon_dist.degree), "Lunar distance from target"),
            "SUNALT": (float(sun_altaz.alt.degree), "Solar altitude"),
            "SUNDIST": (None if sun_dist is None else float(sun_dist.degree), "Solar Distance from Target"),
        }

        return celestial_headers


__all__ = ["BaseTelescope"]
