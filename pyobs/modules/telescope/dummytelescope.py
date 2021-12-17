import asyncio
import logging
import threading
from typing import Tuple, List, Dict, Any, TYPE_CHECKING, Optional

from astropy.coordinates import SkyCoord
import astropy.units as u

from pyobs.events import FilterChangedEvent, OffsetsRaDecEvent
from pyobs.interfaces import IFocuser, IFitsHeaderBefore, IFilters, ITemperatures, IOffsetsRaDec
from pyobs.mixins.fitsnamespace import FitsNamespaceMixin
from pyobs.modules.telescope.basetelescope import BaseTelescope
from pyobs.modules import timeout
from pyobs.utils.enums import MotionStatus
from pyobs.utils.threads import LockWithAbort
from pyobs.utils.time import Time
if TYPE_CHECKING:
    from pyobs.utils.simulation import SimWorld


log = logging.getLogger(__name__)


class DummyTelescope(BaseTelescope, IOffsetsRaDec, IFocuser, IFilters, IFitsHeaderBefore, ITemperatures,
                     FitsNamespaceMixin):
    """A dummy telescope for testing."""
    __module__ = 'pyobs.modules.telescope'

    def __init__(self, world: Optional['SimWorld'] = None, **kwargs: Any):
        """Creates a new dummy telescope."""
        BaseTelescope.__init__(self, **kwargs, motion_status_interfaces=['ITelescope', 'IFocuser', 'IFilters'])
        FitsNamespaceMixin.__init__(self, **kwargs)

        # init world and get telescope
        from pyobs.utils.simulation import SimWorld
        self._world = world if world is not None else \
            self.add_child_object(SimWorld)
        self._telescope = self._world.telescope

        # automatically send status updates
        self._telescope.status_callback = self._change_motion_status

        # some multi-threading stuff
        self._lock_focus = threading.Lock()
        self._abort_focus = threading.Event()

    async def open(self) -> None:
        """Open module."""
        await BaseTelescope.open(self)

        # subscribe to events
        if self.comm:
            await self.comm.register_event(FilterChangedEvent)
            await self.comm.register_event(OffsetsRaDecEvent)

        # init status
        await self._change_motion_status(MotionStatus.IDLE)

    async def _move_radec(self, ra: float, dec: float, abort_event: threading.Event) -> None:
        """Actually starts tracking on given coordinates. Must be implemented by derived classes.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.
            abort_event: Event that gets triggered when movement should be aborted.

        Raises:
            Exception: On any error.
        """

        # start slewing
        await self.__move(ra, dec, abort_event)

    async def _move_altaz(self, alt: float, az: float, abort_event: threading.Event) -> None:
        """Actually moves to given coordinates. Must be implemented by derived classes.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.
            abort_event: Event that gets triggered when movement should be aborted.

        Raises:
            Exception: On error.
        """

        # alt/az coordinates to ra/dec
        coords = SkyCoord(alt=alt * u.degree, az=az * u.degree, obstime=Time.now(),
                          location=self.location, frame='altaz')
        icrs = coords.icrs

        # start slewing
        await self.__move(icrs.ra.degree, icrs.dec.degree, abort_event)

    async def __move(self, ra: float, dec: float, abort_event: threading.Event) -> None:
        """Simulate move.

       Args:
           ra: RA in deg to track.
           dec: Dec in deg to track.
           abort_event: Event that gets triggered when movement should be aborted.

       Raises:
           Exception: On any error.
       """

        # simulate slew
        self._telescope.move_ra_dec(SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame='icrs'))

        # wait for it
        while self._telescope.status == MotionStatus.SLEWING and not abort_event.is_set() and not self.closing.is_set():
            await asyncio.sleep(1)

    async def get_focus(self, **kwargs: Any) -> float:
        """Return current focus.

        Returns:
            Current focus.
        """
        return self._telescope.focus

    @timeout(60)
    async def set_focus(self, focus: float, **kwargs: Any) -> None:
        """Sets new focus.

        Args:
            focus: New focus value.

        Raises:
            InterruptedError: If focus was interrupted.
            AcquireLockFailed: If current motion could not be aborted.
        """

        # acquire lock
        with LockWithAbort(self._lock_focus, self._abort_focus):
            log.info("Setting focus to %.2f..." % focus)
            await self._change_motion_status(MotionStatus.SLEWING, interface='IFocuser')
            ifoc = self._telescope.focus * 1.
            dfoc = (focus - ifoc) / 300.
            for i in range(300):
                # abort?
                if self._abort_focus.is_set():
                    raise InterruptedError('Setting focus was interrupted.')

                # move focus and sleep a little
                self._telescope.focus = ifoc + i * dfoc
                await asyncio.sleep(0.01)
            await self._change_motion_status(MotionStatus.POSITIONED, interface='IFocuser')
            self._telescope.focus = focus

    async def list_filters(self, **kwargs: Any) -> List[str]:
        """List available filters.

        Returns:
            List of available filters.
        """
        return self._telescope.filters

    async def get_filter(self, **kwargs: Any) -> str:
        """Get currently set filter.

        Returns:
            Name of currently set filter.
        """
        return self._telescope.filter

    async def set_filter(self, filter_name: str, **kwargs: Any) -> None:
        """Set the current filter.

        Args:
            filter_name: Name of filter to set.

        Raises:
            ValueError: If binning could not be set.
        """

        # log and send event
        if filter_name != self._telescope.filter:
            # set it
            logging.info('Setting filter to %s', filter_name)
            await self._change_motion_status(MotionStatus.SLEWING, interface='IFilters')
            await asyncio.sleep(3)
            await self._change_motion_status(MotionStatus.POSITIONED, interface='IFilters')
            self._telescope.filter = filter_name

            # send event
            await self.comm.send_event(FilterChangedEvent(filter_name))
            logging.info('New filter set.')

    @timeout(60)
    async def init(self, **kwargs: Any) -> None:
        """Initialize telescope.

        Raises:
            ValueError: If telescope could not be initialized.
        """

        # INIT, wait a little, then IDLE
        log.info('Initializing telescope...')
        await self._change_motion_status(MotionStatus.INITIALIZING)
        await asyncio.sleep(5)
        await self._change_motion_status(MotionStatus.IDLE)
        log.info('Telescope initialized.')

    @timeout(60)
    async def park(self, **kwargs: Any) -> None:
        """Park telescope.

        Raises:
            ValueError: If telescope could not be parked.
        """

        # PARK, wait a little, then PARKED
        log.info('Parking telescope...')
        await self._change_motion_status(MotionStatus.PARKING)
        await asyncio.sleep(5)
        await self._change_motion_status(MotionStatus.PARKED)
        log.info('Telescope parked.')

    async def set_offsets_radec(self, dra: float, ddec: float, **kwargs: Any) -> None:
        """Move an RA/Dec offset.

        Args:
            dra: RA offset in degrees.
            ddec: Dec offset in degrees.

        Raises:
            ValueError: If offset could not be set.
        """
        log.info("Moving offset dra=%.5f, ddec=%.5f", dra, ddec)
        await self.comm.send_event(OffsetsRaDecEvent(ra=dra, dec=ddec))
        self._telescope.set_offsets(dra, ddec)

    async def get_offsets_radec(self, **kwargs: Any) -> Tuple[float, float]:
        """Get RA/Dec offset.

        Returns:
            Tuple with RA and Dec offsets.
        """
        return self._telescope.offsets

    async def get_radec(self, **kwargs: Any) -> Tuple[float, float]:
        """Returns current RA and Dec.

        Returns:
            Tuple of current RA and Dec in degrees.
        """
        return float(self._telescope.position.ra.degree), float(self._telescope.position.dec.degree)

    async def get_altaz(self, **kwargs: Any) -> Tuple[float, float]:
        """Returns current Alt and Az.

        Returns:
            Tuple of current Alt and Az in degrees.
        """
        if self.observer is not None:
            alt_az = self.observer.altaz(Time.now(), self._telescope.position)
            return float(alt_az.alt.degree), float(alt_az.az.degree)
        else:
            raise ValueError('No observer given.')

    async def get_fits_header_before(self, namespaces: Optional[List[str]] = None, **kwargs: Any) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # fetch from BaseTelescope
        hdr = await BaseTelescope.get_fits_header_before(self)

        # focus
        hdr['TEL-FOCU'] = (self._telescope.focus, 'Focus position [mm]')

        # finished
        return self._filter_fits_namespace(hdr, namespaces=namespaces, **kwargs)

    async def stop_motion(self, device: Optional[str] = None, **kwargs: Any) -> None:
        """Stop the motion.

        Args:
            device: Name of device to stop, or None for all.
        """
        pass

    async def get_focus_offset(self, **kwargs: Any) -> float:
        """Return current focus offset.

        Returns:
            Current focus offset.
        """
        return 0

    async def get_temperatures(self, **kwargs: Any) -> Dict[str, float]:
        """Returns all temperatures measured by this module.

        Returns:
            Dict containing temperatures.
        """

        return {
            'M1': 10.,
            'M2': 12.
        }

    async def set_focus_offset(self, offset: float, **kwargs: Any) -> None:
        log.error('Not implemented')

    async def is_ready(self, **kwargs: Any) -> bool:
        log.error('Not implemented')
        return True


__all__ = ['DummyTelescope']
