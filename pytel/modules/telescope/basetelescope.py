import threading
from astropy.coordinates import SkyCoord
import astropy.units as u

from pytel.interfaces import ITelescope
from pytel import PytelModule
from pytel.modules import timeout
from pytel.utils.threads import LockWithAbort


class BaseTelescope(PytelModule, ITelescope):
    """Base class for telescopes."""

    def __init__(self, fits_headers: dict = None, *args, **kwargs):
        """Initialize a new base telescope."""
        PytelModule.__init__(self, *args, **kwargs)

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

        """
            'CRVAL1': ('POSITION.EQUATORIAL.RA_J2000', 'Right ascension of telescope [degrees]'),
            'CRVAL2': ('POSITION.EQUATORIAL.DEC_J2000', 'Declination of telescope [degrees]'),
            'TEL-RA': ('POSITION.EQUATORIAL.RA_J2000', 'Right ascension of telescope [degrees]'),
            'TEL-DEC': ('POSITION.EQUATORIAL.DEC_J2000', 'Declination of telescope [degrees]'),
            'TEL-ZD': ('POSITION.HORIZONTAL.ZD', 'Telescope zenith distance [degrees]'),
            'TEL-ALT': ('POSITION.HORIZONTAL.ALT', 'Telescope altitude [degrees]'),
            'TEL-AZ': ('POSITION.HORIZONTAL.AZ', 'Telescope azimuth [degrees]'),
            'TEL-FOCU': ('POSITION.INSTRUMENTAL.FOCUS.REALPOS', 'Focus position [mm]'),
            'TEL-ROT': ('POSITION.INSTRUMENTAL.DEROTATOR[2].REALPOS', 'Derotator instrumental position at end [deg]'),
            'DEROTOFF': ('POINTING.SETUP.DEROTATOR.OFFSET', 'Derotator offset [deg]'),
            'AZOFF': ('POSITION.INSTRUMENTAL.AZ.OFFSET', 'Azimuth offset'),
            'ALTOFF': ('POSITION.INSTRUMENTAL.ZD.OFFSET', 'Altitude offset')
        """
        # positions
        try:
            ra, dec = self.get_ra_dec()
            hdr['TEL-RA'] = (ra, 'Right ascension of telescope [degrees]')
            hdr['TEL-DEC'] = (dec, 'Declination of telescope [degrees]')
        except NotImplementedError:
            pass
        try:
            alt, az = self.get_alt_az()
            hdr['TEL-ALT'] = (alt, 'Telescope altitude [degrees]')
            hdr['TEL-AZ'] = (az, 'Telescope azimuth [degrees]')
        except NotImplementedError:
            pass

        # calculate missing parts
        # TODO
        if 'TEL-ALT' in hdr and 'TEL-RA' not in hdr:
            hdr['TEL-RA'] = (0., 'Right ascension of telescope [degrees]')
            hdr['TEL-DEC'] = (0., 'Declination of telescope [degrees]')
        if 'TEL-RA' in hdr and 'TEL-ALT' not in hdr:
            hdr['TEL-ALT'] = (0., 'Telescope altitude [degrees]')
            hdr['TEL-AZ'] = (0., 'Telescope azimuth [degrees]')

        # derived headers
        hdr['CRVAL1'] = hdr['TEL-RA']
        hdr['CRVAL2'] = hdr['TEL-DEC']
        hdr['TEL-ZD'] = (90. - hdr['TEL-ALT'][0], 'Telescope zenith distance [degrees]')
        # hdr['AIRMASS'] = ...

        # create sky coordinates
        c = SkyCoord(ra=hdr['TEL-RA'][0] * u.deg, dec=hdr['TEL-DEC'][0] * u.deg, frame='icrs')

        # convert to sexagesimal
        hdr['RA'] = (str(c.ra.to_string(sep=':', unit=u.hour, pad=True)), 'Right ascension of object')
        hdr['DEC'] = (str(c.dec.to_string(sep=':', unit=u.deg, pad=True)), 'Declination of object')

        # add static fits headers
        for key, value in self._fits_headers.items():
            hdr[key] = tuple(value)

        # finish
        return hdr


__all__ = ['BaseTelescope']
