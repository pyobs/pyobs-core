import threading
from typing import Dict, Any, Tuple, Union, List

from astropy.coordinates import SkyCoord, ICRS, AltAz
import astropy.units as u
import logging

from pyobs.interfaces import ITelescope, IMotion, IFitsHeaderProvider
from pyobs import Module
from pyobs.mixins import MotionStatusMixin, WeatherAwareMixin, WaitForMotionMixin
from pyobs.modules import timeout
from pyobs.utils.threads import LockWithAbort
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class BaseTelescope(WeatherAwareMixin, MotionStatusMixin, WaitForMotionMixin, ITelescope, IFitsHeaderProvider, Module):
    """Base class for telescopes."""

    def __init__(self, fits_headers: dict = None, min_altitude: float = 10, wait_for_dome: str = None, *args, **kwargs):
        """Initialize a new base telescope.

        Args:
            fits_headers: Additional FITS headers to send.
            min_altitude: Minimal altitude for telescope.
            wait_for_dome: Name of dome module to wait for.
        """
        Module.__init__(self, *args, **kwargs)

        # store
        self._fits_headers = fits_headers if fits_headers is not None else {}
        self._min_altitude = min_altitude

        # some multi-threading stuff
        self._lock_moving = threading.Lock()
        self._abort_move = threading.Event()

        # celestial status
        self._celestial_lock = threading.RLock()
        self._celestial_headers: Dict[str, Any] = {}

        # add thread func
        self._add_thread_func(self._celestial, True)

        # init mixins
        WeatherAwareMixin.__init__(self, *args, **kwargs)
        MotionStatusMixin.__init__(self, *args, **kwargs)
        WaitForMotionMixin.__init__(self,
                                    wait_for_modules=None if wait_for_dome is None else [wait_for_dome],
                                    wait_for_timeout=60000,
                                    wait_for_states=[IMotion.Status.POSITIONED, IMotion.Status.TRACKING])

    def open(self):
        """Open module."""
        Module.open(self)

        # open mixins
        WeatherAwareMixin.open(self)
        MotionStatusMixin.open(self)

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

    def _move_radec(self, ra: float, dec: float, abort_event: threading.Event):
        """Actually starts tracking on given coordinates. Must be implemented by derived classes.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.
            abort_event: Event that gets triggered when movement should be aborted.

        Raises:
            Exception: On any error.
        """
        raise NotImplementedError

    @timeout(1200)
    def move_radec(self, ra: float, dec: float, track: bool = True, *args, **kwargs):
        """Starts tracking on given coordinates.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.
            track: Whether the device should start tracking on the given coordinates.

        Raises:
            ValueError: If device could not track.
        """

        # check observer
        if self.observer is None:
            raise ValueError('No observer given.')

        # to alt/az
        ra_dec = SkyCoord(ra * u.deg, dec * u.deg, frame=ICRS)
        alt_az = self.observer.altaz(Time.now(), ra_dec)

        # check altitude
        if alt_az.alt.degree < self._min_altitude:
            raise ValueError('Destination altitude below limit.')

        # acquire lock
        with LockWithAbort(self._lock_moving, self._abort_move):
            # log and event
            self._change_motion_status(IMotion.Status.SLEWING)
            log.info("Moving telescope to RA=%s (%.5f°), Dec=%s (%.5f°)...",
                     ra_dec.ra.to_string(sep=':', unit=u.hour, pad=True), ra,
                     ra_dec.dec.to_string(sep=':', unit=u.deg, pad=True), dec)

            # track telescope
            self._move_radec(ra, dec, abort_event=self._abort_move)
            log.info('Reached destination')

            # move dome, if exists
            self._wait_for_motion(self._abort_move)

            # finish slewing
            self._change_motion_status(IMotion.Status.TRACKING)

            # update headers now
            threading.Thread(target=self._update_celestial_headers).start()
            log.info('Finished moving telescope.')

    def _move_altaz(self, alt: float, az: float, abort_event: threading.Event):
        """Actually moves to given coordinates. Must be implemented by derived classes.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.
            abort_event: Event that gets triggered when movement should be aborted.

        Raises:
            Exception: On error.
        """
        raise NotImplementedError

    @timeout(1200)
    def move_altaz(self, alt: float, az: float, *args, **kwargs):
        """Moves to given coordinates.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.

        Raises:
            Exception: On error.
            AcquireLockFailed: If current motion could not be aborted.
        """

        # check altitude
        if alt < self._min_altitude:
            raise ValueError('Destination altitude below limit.')

        # acquire lock
        with LockWithAbort(self._lock_moving, self._abort_move):
            # log and event
            log.info("Moving telescope to Alt=%.2f°, Az=%.2f°...", alt, az)
            self._change_motion_status(IMotion.Status.SLEWING)

            # move telescope
            self._move_altaz(alt, az, abort_event=self._abort_move)
            log.info('Reached destination')

            # move dome, if exists
            self._wait_for_motion(self._abort_move)

            # finish slewing
            self._change_motion_status(IMotion.Status.POSITIONED)

            # update headers now
            threading.Thread(target=self._update_celestial_headers).start()
            log.info('Finished moving telescope.')

    def get_fits_headers(self, namespaces: List[str] = None, *args, **kwargs) -> Dict[str, Tuple[Any, str]]:
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
            ra, dec = self.get_radec()
            coords_ra_dec = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame=ICRS)
            alt, az = self.get_altaz()
            coords_alt_az = SkyCoord(alt=alt * u.deg, az=az * u.deg, frame=AltAz)

        except Exception as e:
            log.warning('Could not fetch telescope position: %s', e)
            coords_ra_dec, coords_alt_az = None, None

        # set coordinate headers
        if coords_ra_dec is not None:
            hdr['TEL-RA'] = (float(coords_ra_dec.ra.degree), 'Right ascension of telescope [degrees]')
            hdr['TEL-DEC'] = (float(coords_ra_dec.dec.degree), 'Declination of telescope [degrees]')
            hdr['CRVAL1'] = hdr['TEL-RA']
            hdr['CRVAL2'] = hdr['TEL-DEC']
        if coords_alt_az is not None:
            hdr['TEL-ALT'] = (float(coords_alt_az.alt.degree), 'Telescope altitude [degrees]')
            hdr['TEL-AZ'] = (float(coords_alt_az.az.degree), 'Telescope azimuth [degrees]')
            hdr['TEL-ZD'] = (90. - hdr['TEL-ALT'][0], 'Telescope zenith distance [degrees]')
            hdr['AIRMASS'] = (float(coords_alt_az.secz.value), 'Airmass of observation start')

        # convert to sexagesimal
        if coords_ra_dec is not None:
            hdr['RA'] = (str(coords_ra_dec.ra.to_string(sep=':', unit=u.hour, pad=True)), 'Right ascension of object')
            hdr['DEC'] = (str(coords_ra_dec.dec.to_string(sep=':', unit=u.deg, pad=True)), 'Declination of object')

        # site location
        if self.observer is not None:
            hdr['LATITUDE'] = (float(self.observer.location.lat.degree), 'Latitude of telescope [deg N]')
            hdr['LONGITUD'] = (float(self.observer.location.lon.degree), 'Longitude of telescope [deg E]')
            hdr['HEIGHT'] = (float(self.observer.location.height.value), 'Altitude of telescope [m]')

        # add static fits headers
        for key, value in self._fits_headers.items():
            hdr[key] = tuple(value)

        # add celestial headers
        for key, value in self._celestial_headers.items():
            hdr[key] = tuple(value)

        # finish
        return hdr

    def _celestial(self):
        """Thread for continuously calculating positions and distances to celestial objects like moon and sun."""
 
        # wait a little
        self.closing.wait(10)

        # run until closing
        while not self.closing.is_set():
            # update headers
            self._update_celestial_headers()

            # sleep a little
            self.closing.wait(30)

    def _update_celestial_headers(self):
        """Calculate positions and distances to celestial objects like moon and sun."""
        # get now
        now = Time.now()

        # get telescope alt/az
        try:
            alt, az = self.get_altaz()
            tel_altaz = SkyCoord(alt=alt * u.deg, az=az * u.deg, frame='altaz')
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
        with self._celestial_lock:
            self._celestial_headers = {
                'MOONALT': (float(moon_altaz.alt.degree), 'Lunar altitude'),
                'MOONFRAC': (float(moon_frac), 'Fraction of the moon illuminated'),
                'MOONDIST': (None if moon_dist is None else float(moon_dist.degree), 'Lunar distance from target'),
                'SUNALT': (float(sun_altaz.alt.degree), 'Solar altitude'),
                'SUNDIST': (None if sun_dist is None else float(sun_dist.degree), 'Solar Distance from Target')
            }


__all__ = ['BaseTelescope']
