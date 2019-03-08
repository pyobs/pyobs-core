import threading
from astropy.coordinates import SkyCoord
import astropy.units as u

from pyobs.interfaces import ITelescope
from pyobs import PyObsModule
from pyobs.modules import timeout
from pyobs.utils.threads import LockWithAbort


class BaseTelescope(PyObsModule, ITelescope):
    """Base class for telescopes."""

    def __init__(self, fits_headers: dict = None, *args, **kwargs):
        """Initialize a new base telescope."""
        PyObsModule.__init__(self, *args, **kwargs)

        # additional fits headers
        self._fits_headers = fits_headers if fits_headers is not None else {}

        # some multi-threading stuff
        self._lock_moving = threading.Lock()
        self._abort_move = threading.Event()

    def status(self, *args, **kwargs) -> dict:
        """Returns current status.

        Returns:
            dict: A dictionary with status values.
        """

        # init status
        status = {'ITelescope': {}}

        # get current telescope status
        status['ITelescope']['Status'] = self.get_motion_status()

        # get position
        status['ITelescope']['Position'] = {}
        try:
            ra, dec = self.get_ra_dec()
            status['ITelescope']['Position']['RA'] = ra
            status['ITelescope']['Position']['Dec'] = dec
        except NotImplementedError:
            pass
        try:
            alt, az = self.get_alt_az()
            status['ITelescope']['Position']['Alt'] = alt
            status['ITelescope']['Position']['Az'] = az
        except NotImplementedError:
            pass

        # finished
        return status

    def init(self, *args, **kwargs):
        """Initialize telescope.

        Raises:
            ValueError: If telescope could not be initialized.
        """
        raise NotImplementedError

    def park(self, *args, **kwargs):
        """Park telescope.

        Raises:
            ValueError: If telescope could not be parked.
        """
        raise NotImplementedError

    def reset_offset(self, *args, **kwargs):
        """Reset Alt/Az offset.

        Raises:
            ValueError: If offset could not be reset.
        """
        raise NotImplementedError

    def _track(self, ra: float, dec: float, abort_event: threading.Event):
        """Actually starts tracking on given coordinates. Must be implemented by derived classes.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.
            abort_event: Event that gets triggered when movement should be aborted.

        Raises:
            Exception: On any error.
        """
        raise NotImplementedError

    @timeout(60000)
    def track(self, ra: float, dec: float, *args, **kwargs):
        """Starts tracking on given coordinates.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.

        Raises:
            ValueError: If telescope could not track.
        """

        # acquire lock
        with LockWithAbort(self._lock_moving, self._abort_move):
            # track telescope
            return self._track(ra, dec, abort_event=self._abort_move)

    def offset(self, dalt: float, daz: float, *args, **kwargs):
        """Move an Alt/Az offset, which will be reset on next call of track.

        Args:
            dalt: Altitude offset in degrees.
            daz: Azimuth offset in degrees.

        Raises:
            ValueError: If offset could not be set.
        """
        raise NotImplementedError

    def _move(self, alt: float, az: float, abort_event: threading.Event):
        """Actually moves to given coordinates. Must be implemented by derived classes.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.
            abort_event: Event that gets triggered when movement should be aborted.

        Raises:
            Exception: On error.
        """
        raise NotImplementedError

    @timeout(60000)
    def move(self, alt: float, az: float, *args, **kwargs):
        """Moves to given coordinates.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.

        Raises:
            Exception: On error.
        """

        # acquire lock
        with LockWithAbort(self._lock_moving, self._abort_move):
            # move telescope
            return self._move(alt, az, abort_event=self._abort_move)

    def get_fits_headers(self, *args, **kwargs) -> dict:
        """Returns FITS header for the current status of the telescope.

        Returns:
            Dictionary containing FITS headers.
        """

        # define base header
        hdr = {}

        # positions
        ra, dec = self.get_ra_dec()
        coords_ra_dec = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame='icrs')
        alt, az = self.get_alt_az()
        coords_alt_az = SkyCoord(alt=alt * u.deg, az=az * u.deg, frame='altaz')

        # set coordinate headers
        hdr['TEL-RA'] = (coords_ra_dec.ra.degree, 'Right ascension of telescope [degrees]')
        hdr['TEL-DEC'] = (coords_ra_dec.dec.degree, 'Declination of telescope [degrees]')
        hdr['CRVAL1'] = hdr['TEL-RA']
        hdr['CRVAL2'] = hdr['TEL-DEC']
        hdr['TEL-ALT'] = (coords_alt_az.alt.degree, 'Telescope altitude [degrees]')
        hdr['TEL-AZ'] = (coords_alt_az.az.degree, 'Telescope azimuth [degrees]')
        hdr['TEL-ZD'] = (90. - hdr['TEL-ALT'][0], 'Telescope zenith distance [degrees]')
        hdr['AIRMASS'] = (coords_alt_az.secz.value, 'airmass of observation start')

        # convert to sexagesimal
        hdr['RA'] = (str(coords_ra_dec.ra.to_string(sep=':', unit=u.hour, pad=True)), 'Right ascension of object')
        hdr['DEC'] = (str(coords_ra_dec.dec.to_string(sep=':', unit=u.deg, pad=True)), 'Declination of object')

        # add static fits headers
        for key, value in self._fits_headers.items():
            hdr[key] = tuple(value)

        # finish
        return hdr


__all__ = ['BaseTelescope']
