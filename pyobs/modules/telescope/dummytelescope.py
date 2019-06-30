import logging
import threading
import time
from astropy.coordinates import SkyCoord
import astropy.units as u

from pyobs.events import FilterChangedEvent
from pyobs.interfaces import IFocuser, IFitsHeaderProvider, IFilters, IFocusModel, IMotion
from pyobs.modules.telescope.basetelescope import BaseTelescope
from pyobs.modules import timeout
from pyobs.utils.threads import LockWithAbort
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class DummyTelescope(BaseTelescope, IFocuser, IFilters, IFitsHeaderProvider, IFocusModel):
    """A dummy telescope for testing."""

    def __init__(self, *args, **kwargs):
        """Creates a new dummy telescope."""
        BaseTelescope.__init__(self, *args, **kwargs)

        # init telescope
        self._images = {}
        self._position = {'ra': 12.12, 'dec': 45.45}
        self._focus = 52.
        self._filter = 'V'

        # some multi-threading stuff
        self._lock_focus = threading.Lock()
        self._abort_focus = threading.Event()

    def open(self):
        """Open module."""
        BaseTelescope.open(self)

        # subscribe to events
        if self.comm:
            self.comm.register_event(FilterChangedEvent)

    def _track(self, ra: float, dec: float, abort_event: threading.Event):
        """Actually starts tracking on given coordinates. Must be implemented by derived classes.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.
            abort_event: Event that gets triggered when movement should be aborted.

        Raises:
            Exception: On any error.
        """

        # start slewing
        self._change_motion_status(IMotion.Status.SLEWING)

        # simulate slew
        ira = self._position['ra'] * 1.
        idec = self._position['dec'] * 1.
        dra = (ra - ira) / 100.
        ddec = (dec - idec) / 100.
        for i in range(100):
            # abort?
            if abort_event.is_set():
                self._change_motion_status(IMotion.Status.IDLE)
                raise ValueError('Movement was aborted.')

            # move
            self._position['ra'] = ira + i * dra
            self._position['dec'] = idec + i * ddec

            # sleep a little
            abort_event.wait(0.1)

        # finish slewing
        self._position['ra'] = ra
        self._position['dec'] = dec
        self._change_motion_status(IMotion.Status.TRACKING)

    def _move(self, alt: float, az: float, abort_event: threading.Event):
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

        # track
        self._track(icrs.ra.degree, icrs.dec.degree, abort_event)

        # set telescope to idle
        self._change_motion_status(IMotion.Status.IDLE)

    def get_focus(self, *args, **kwargs) -> float:
        """Return current focus.

        Returns:
            Current focus.
        """
        return self._focus

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
            ifoc = self._focus * 1.
            dfoc = (focus - ifoc) / 300.
            for i in range(300):
                # abort?
                if self._abort_focus.is_set():
                    raise InterruptedError('Setting focus was interrupted.')

                # move focus and sleep a little
                self._focus = ifoc + i * dfoc
                time.sleep(0.01)
            self._focus = focus

    def set_optimal_focus(self, *args, **kwargs):
        """Sets optimal focus.

        Raises:
            InterruptedError: If focus was interrupted.
        """
        log.info('Setting optimal focus...')
        self.set_focus(42.0)

    def list_filters(self, *args, **kwargs) -> list:
        """List available filters.

        Returns:
            List of available filters.
        """
        return ['U', 'B', 'V', 'R', 'I']

    def get_filter(self, *args, **kwargs) -> str:
        """Get currently set filter.

        Returns:
            Name of currently set filter.
        """
        return self._filter

    def set_filter(self, filter_name: str, *args, **kwargs):
        """Set the current filter.

        Args:
            filter_name: Name of filter to set.

        Raises:
            ValueError: If binning could not be set.
        """

        # log and send event
        if filter_name != self._filter:
            # set it
            logging.info('Setting filter to %s', filter_name)
            time.sleep(3)
            self._filter = filter_name

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

    @timeout(60000)
    def park(self, *args, **kwargs):
        """Park telescope.

        Raises:
            ValueError: If telescope could not be parked.
        """

        # PARK, wait a little, then PARKED
        self._change_motion_status(IMotion.Status.INITIALIZING)
        time.sleep(5.)
        self._change_motion_status(IMotion.Status.PARKED)

    def reset_offset(self, *args, **kwargs):
        """Reset Alt/Az offset.

        Raises:
            ValueError: If offset could not be reset.
        """
        log.info("Resetting offsets")

    def offset_altaz(self, dalt: float, daz: float, *args, **kwargs):
        """Move an Alt/Az offset, which will be reset on next call of track.

        Args:
            dalt: Altitude offset in degrees.
            daz: Azimuth offset in degrees.

        Raises:
            ValueError: If offset could not be set.
        """
        log.info("Moving offset dalt=%.5f, daz=%.5f", dalt, daz)

    def get_ra_dec(self) -> (float, float):
        """Returns current RA and Dec.

        Returns:
            Tuple of current RA and Dec in degrees.
        """
        return self._position['ra'], self._position['dec']

    def get_alt_az(self) -> (float, float):
        """Returns current Alt and Az.

        Returns:
            Tuple of current Alt and Az in degrees.
        """
        ra_dec = SkyCoord(ra=self._position['ra'] * u.deg, dec=self._position['dec'] * u.deg, frame='icrs')
        alt_az = self.observer.altaz(Time.now(), ra_dec)
        return alt_az.alt.degree, alt_az.az.degree

    def get_fits_headers(self, *args, **kwargs) -> dict:
        """Returns FITS header for the current status of the telescope.

        Returns:
            Dictionary containing FITS headers.
        """

        # fetch from BaseTelescope
        hdr = BaseTelescope.get_fits_headers(self)

        # focus
        hdr['TEL-FOCU'] = (self._focus, 'Focus position [mm]')

        # filter
        hdr['FILTER'] = (self._filter, 'Focus position [mm]')

        # finished
        return hdr

    def stop_motion(self, device: str = None, *args, **kwargs):
        """Stop the motion.

        Args:
            device: Name of device to stop, or None for all.
        """
        pass


__all__ = ['DummyTelescope']
