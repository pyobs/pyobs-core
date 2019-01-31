import logging
import threading
import time
from astropy.coordinates import SkyCoord
from astropy import units as u

from pytel.interfaces import IFocuser, IFitsHeaderProvider, IFilters, IFocusModel
from pytel.modules.telescope.basetelescope import BaseTelescope
from pytel.modules import timeout
from pytel.utils.threads import LockWithAbort


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

        # init status
        self.telescope_status = BaseTelescope.Status.PARKED

        # some multi-threading stuff
        self._lock_focus = threading.Lock()
        self._abort_focus = threading.Event()

    def status(self, *args, **kwargs) -> dict:
        """Returns current status.

        Returns:
            dict: A dictionary with status values.
        """

        # get status
        s = super().status(*args, **kwargs)

        # telescope
        s['ITelescope'] = {
            'Status': self.telescope_status.value,
            'Position': {
                'RA': self._position['ra'],
                'Dec': self._position['dec']
            },
            'Temperatures': {
                'M1': 17.,
                'M2': 18.
            }
        }

        # focus
        s['IFocuser'] = {
            'Focus': self._focus
        }

        # filter
        s['IFilter'] = {
            'Filter': self._filter
        }

        # finished
        return s

    def get_fits_headers(self, *args, **kwargs) -> dict:
        """Returns FITS header for the current status of the telescope.

        Returns:
            Dictionary containing FITS headers.
        """

        # define base header
        hdr = {
            'OBJRA': (self._position['ra'], 'Declination of object [degrees]'),
            'OBJDEC': (self._position['dec'], 'Right ascension of object [degrees]'),
            'TEL-FOCU': (self._focus, 'Focus position [mm]')
        }

        # create sky coordinates
        c = SkyCoord(ra=hdr['OBJRA'][0] * u.deg, dec=hdr['OBJDEC'][0] * u.deg, frame='icrs')

        # convert to sexagesimal
        hdr['RA'] = (str(c.ra.to_string(sep=':', unit=u.hour, pad=True)), 'Right ascension of object')
        hdr['DEC'] = (str(c.dec.to_string(sep=':', unit=u.deg, pad=True)), 'Declination of object')

        # finish
        return hdr

    def _track(self, ra: float, dec: float, abort_event: threading.Event) -> bool:
        """Actually starts tracking on given coordinates.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.
            abort_event: Event that gets triggered when movement should be aborted.

        Returns:
            Success or not.
        """

        # start slewing
        log.info("Moving telescope to RA=%.2f, Dec=%.2f...", ra, dec)
        self.telescope_status = BaseTelescope.Status.SLEWING

        # simulate slew
        ira = self._position['ra'] * 1.
        idec = self._position['dec'] * 1.
        dra = (ra - ira) / 1000.
        ddec = (dec - idec) / 1000.
        for i in range(1000):
            # abort?
            if abort_event.is_set():
                self.telescope_status = BaseTelescope.Status.IDLE
                return False

            # move
            self._position['ra'] = ira + i * dra
            self._position['dec'] = idec + i * ddec

            # sleep a little
            abort_event.wait(1.)

        # finish slewing
        self._position['ra'] = ra
        self._position['dec'] = dec
        self.telescope_status = BaseTelescope.Status.TRACKING
        log.info('Reached destination')
        return True

    def _move(self, alt: float, az: float, abort_event: threading.Event) -> bool:
        """Actually moves to given coordinates. Must be implemented by derived classes.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.
            abort_event: Event that gets triggered when movement should be aborted.

        Returns:
            Success or not.
        """
        pass

    def get_focus(self, *args, **kwargs) -> float:
        """Return current focus.

        Returns:
            Current focus.
        """
        return self._focus

    @timeout(60000)
    def set_focus(self, focus: float, *args, **kwargs) -> bool:
        """Sets new focus.

        Args:
            focus: New focus value.

        Returns:
            Success or not.
        """

        # acquire lock
        with LockWithAbort(self._lock_focus, self._abort_focus):
            log.info("Setting focus to %.2f..." % focus)
            ifoc = self._focus * 1.
            dfoc = (focus - ifoc) / 300.
            for i in range(300):
                # abort?
                if self._abort_focus.is_set():
                    return False

                # move focus and sleep a little
                self._focus = ifoc + i * dfoc
                time.sleep(0.01)
            self._focus = focus

            # success
            return True

    def set_optimal_focus(self, *args, **kwargs) -> bool:
        """Sets optimal focus.

        Returns:
            Success or not.
        """
        log.info('Setting optimal focus...')
        return self.set_focus(42.0)

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

    def set_filter(self, filter_name: str, *args, **kwargs) -> bool:
        """Set the current filter.

        Args:
            filter_name: Name of filter to set.

        Returns:
            Success or not.
        """
        logging.info('Setting filter to %s', filter_name)
        self._filter = filter_name
        return True

    @timeout(60000)
    def init(self, *args, **kwargs) -> bool:
        """Initialize telescope.

        Returns:
            Success or not.
        """

        # INIT, wait a little, then IDLE
        self.telescope_status = BaseTelescope.Status.INITPARK
        time.sleep(5.)
        self.telescope_status = BaseTelescope.Status.IDLE
        return True

    @timeout(60000)
    def park(self, *args, **kwargs) -> bool:
        """Park telescope.

        Returns:
            Success or not.
        """

        # PARK, wait a little, then PARKED
        self.telescope_status = BaseTelescope.Status.INITPARK
        time.sleep(5.)
        self.telescope_status = BaseTelescope.Status.PARKED
        return True

    def reset_offset(self, *args, **kwargs) -> bool:
        """Reset Alt/Az offset.

        Returns:
            Success or not.
        """
        log.info("Resetting offsets")
        return True

    def offset(self, dalt: float, daz: float, *args, **kwargs) -> bool:
        """Move an Alt/Az offset, which will be reset on next call of track.

        Args:
            dalt: Altitude offset in degrees.
            daz: Azimuth offset in degrees.
        """
        log.info("Moving offset dalt=%.5f, daz=%.5f", dalt, daz)
        return True


__all__ = ['DummyTelescope']
