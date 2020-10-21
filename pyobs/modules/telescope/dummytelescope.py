import logging
import threading
import time
from astropy.coordinates import SkyCoord
import astropy.units as u

from pyobs.events import FilterChangedEvent, InitializedEvent, TelescopeMovingEvent
from pyobs.interfaces import IFocuser, IFitsHeaderProvider, IFilters, IMotion, IAltAzOffsets, ITemperatures
from pyobs.mixins.fitsnamespace import FitsNamespaceMixin
from pyobs.modules.telescope.basetelescope import BaseTelescope
from pyobs.modules import timeout
from pyobs.utils.simulation.world import SimWorld
from pyobs.utils.threads import LockWithAbort
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class DummyTelescope(BaseTelescope, IAltAzOffsets, IFocuser, IFilters, IFitsHeaderProvider, ITemperatures,
                     FitsNamespaceMixin):
    """A dummy telescope for testing."""

    def __init__(self, world: SimWorld = None, *args, **kwargs):
        """Creates a new dummy telescope."""
        BaseTelescope.__init__(self, *args, **kwargs, motion_status_interfaces=['ITelescope', 'IFocuser', 'IFilters'])
        FitsNamespaceMixin.__init__(self, *args, **kwargs)

        # init world and get telescope
        self._world = world if world is not None else SimWorld()
        self._telescope = self._world.telescope

        # some multi-threading stuff
        self._lock_focus = threading.Lock()
        self._abort_focus = threading.Event()

    def open(self):
        """Open module."""
        BaseTelescope.open(self)

        # subscribe to events
        if self.comm:
            self.comm.register_event(FilterChangedEvent)
            self.comm.register_event(InitializedEvent)
            self.comm.register_event(TelescopeMovingEvent)

        # init status
        self._change_motion_status(IMotion.Status.PARKED)

    def _move_radec(self, ra: float, dec: float, abort_event: threading.Event):
        """Actually starts tracking on given coordinates. Must be implemented by derived classes.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.
            abort_event: Event that gets triggered when movement should be aborted.

        Raises:
            Exception: On any error.
        """

        # send events
        self._change_motion_status(IMotion.Status.SLEWING, interface='ITelescope')
        self.comm.send_event(TelescopeMovingEvent(ra=ra, dec=dec))

        # start slewing
        self.__move(ra, dec, abort_event)

        # finish slewing
        self._change_motion_status(IMotion.Status.TRACKING, interface='ITelescope')

    def _move_altaz(self, alt: float, az: float, abort_event: threading.Event):
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

        # send events
        self._change_motion_status(IMotion.Status.SLEWING, interface='ITelescope')
        self.comm.send_event(TelescopeMovingEvent(alt=alt, az=az))

        # start slewing
        self.__move(icrs.ra.degree, icrs.dec.degree, abort_event)

        # set telescope to idle
        self._change_motion_status(IMotion.Status.IDLE)

    def __move(self, ra: float, dec: float, abort_event: threading.Event):
        """Simulate move.

       Args:
           ra: RA in deg to track.
           dec: Dec in deg to track.
           abort_event: Event that gets triggered when movement should be aborted.

       Raises:
           Exception: On any error.
       """

        # simulate slew
        ira, idec = self._telescope.position.ra.degree, self._telescope.position.dec.degree
        dra = (ra - ira) / 100.
        ddec = (dec - idec) / 100.
        for i in range(100):
            # abort?
            if abort_event.is_set():
                self._change_motion_status(IMotion.Status.IDLE)
                raise ValueError('Movement was aborted.')

            # move
            self._telescope.position = SkyCoord((ira + i * dra) * u.deg, (idec + i * ddec) * u.deg, frame='icrs')

            # sleep a little
            abort_event.wait(0.1)

        # set final coordinates
        self._telescope.position = SkyCoord(ra * u.deg, dec * u.deg, frame='icrs')

    def get_focus(self, *args, **kwargs) -> float:
        """Return current focus.

        Returns:
            Current focus.
        """
        return self._telescope.focus

    @timeout(60000)
    def set_focus(self, focus: float, *args, **kwargs):
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
            self._change_motion_status(IMotion.Status.SLEWING, interface='IFocuser')
            ifoc = self._telescope.focus * 1.
            dfoc = (focus - ifoc) / 300.
            for i in range(300):
                # abort?
                if self._abort_focus.is_set():
                    raise InterruptedError('Setting focus was interrupted.')

                # move focus and sleep a little
                self._telescope.focus = ifoc + i * dfoc
                time.sleep(0.01)
            self._change_motion_status(IMotion.Status.POSITIONED, interface='IFocuser')
            self._telescope.focus = focus

    def list_filters(self, *args, **kwargs) -> list:
        """List available filters.

        Returns:
            List of available filters.
        """
        return self._telescope.filters

    def get_filter(self, *args, **kwargs) -> str:
        """Get currently set filter.

        Returns:
            Name of currently set filter.
        """
        return self._telescope.filter

    def set_filter(self, filter_name: str, *args, **kwargs):
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
            self._change_motion_status(IMotion.Status.SLEWING, interface='IFilters')
            time.sleep(3)
            self._change_motion_status(IMotion.Status.POSITIONED, interface='IFilters')
            self._telescope.filter = filter_name

            # send event
            self.comm.send_event(FilterChangedEvent(filter_name))
            logging.info('New filter set.')

    @timeout(60000)
    def init(self, *args, **kwargs):
        """Initialize telescope.

        Raises:
            ValueError: If telescope could not be initialized.
        """

        # INIT, wait a little, then IDLE
        self._change_motion_status(IMotion.Status.INITIALIZING)
        time.sleep(5.)
        self._change_motion_status(IMotion.Status.IDLE)
        self.comm.send_event(InitializedEvent())

    @timeout(60000)
    def park(self, *args, **kwargs):
        """Park telescope.

        Raises:
            ValueError: If telescope could not be parked.
        """

        # PARK, wait a little, then PARKED
        self._change_motion_status(IMotion.Status.PARKING)
        time.sleep(5.)
        self._change_motion_status(IMotion.Status.PARKED)

    def set_altaz_offsets(self, dalt: float, daz: float, *args, **kwargs):
        """Move an Alt/Az offset, which will be reset on next call of track.

        Args:
            dalt: Altitude offset in degrees.
            daz: Azimuth offset in degrees.

        Raises:
            ValueError: If offset could not be set.
        """
        log.info("Moving offset dalt=%.5f, daz=%.5f", dalt, daz)
        self._telescope.offsets = (dalt, daz)

    def get_altaz_offsets(self, *args, **kwargs) -> (float, float):
        """Get Alt/Az offset.

        Returns:
            Tuple with alt and az offsets.
        """
        return self._telescope.offsets

    def get_radec(self, *args, **kwargs) -> (float, float):
        """Returns current RA and Dec.

        Returns:
            Tuple of current RA and Dec in degrees.
        """
        return float(self._telescope.position.ra.degree), float(self._telescope.position.dec.degree)

    def get_altaz(self, *args, **kwargs) -> (float, float):
        """Returns current Alt and Az.

        Returns:
            Tuple of current Alt and Az in degrees.
        """
        alt_az = self.observer.altaz(Time.now(), self._telescope.position)
        return float(alt_az.alt.degree), float(alt_az.az.degree)

    def get_fits_headers(self, namespaces: list = None, *args, **kwargs) -> dict:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # fetch from BaseTelescope
        hdr = BaseTelescope.get_fits_headers(self)

        # focus
        hdr['TEL-FOCU'] = (self._telescope.focus, 'Focus position [mm]')

        # finished
        return self._filter_fits_namespace(hdr, namespaces, **kwargs)

    def stop_motion(self, device: str = None, *args, **kwargs):
        """Stop the motion.

        Args:
            device: Name of device to stop, or None for all.
        """
        pass

    def get_focus_offset(self, *args, **kwargs) -> float:
        """Return current focus offset.

        Returns:
            Current focus offset.
        """
        return 0

    def get_temperatures(self, *args, **kwargs) -> dict:
        """Returns all temperatures measured by this module.

        Returns:
            Dict containing temperatures.
        """

        return {
            'M1': 10,
            'M2': 12
        }


__all__ = ['DummyTelescope']
