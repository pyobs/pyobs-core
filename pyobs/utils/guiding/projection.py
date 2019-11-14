import logging
import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy.time import Time
from scipy.interpolate import UnivariateSpline
from scipy.optimize import fmin
from astropy.wcs import WCS
import re

from pyobs.interfaces import ITelescope, IEquitorialMount, IAltAzMount, ICamera
from pyobs.utils.images import Image
from pyobs.utils.pid import PID
from .base import BaseGuider


log = logging.getLogger(__name__)


class AutoGuidingProjection(BaseGuider):
    """An auto-guiding system based on comparing collapsed images along the x&y axes with a reference image."""

    def __init__(self, max_offset: float = 10, max_exposure_time: float = 20,
                 max_interval: float = 30, separation_reset: float = 10, pid: bool = False, *args, **kwargs):
        """Initializes a new auto guiding system.

        Args:
            max_offset: Max offset in arcsec to move.
            max_exposure_time: Maximum exposure time in sec for images to analyse.
            max_interval: Maximum interval in sec between to consecutive images to guide.
            separation_reset: Min separation in arcsec between two consecutive images that triggers a reset.
            pid: Whether to use a PID for guiding.
        """

        # store
        self._max_offset = max_offset
        self._max_exposure_time = max_exposure_time
        self._max_interval = max_interval
        self._separation_reset = separation_reset
        self._pid = pid

        # variables
        self._ref_image = None
        self._ref_header = None
        self._last_header = None
        self._pid_ra = None
        self._pid_dec = None
        self._loop_closed = False

    def __call__(self, image: Image, telescope: ITelescope, location: EarthLocation):
        """Processes an image.

        Args:
            image: Image to process.
            telescope: Telescope to guide
            location: Location of observer
        """

        # we only accept OBJECT images
        if image.header['IMAGETYP'] != 'object':
            return

        # process it
        if self._ref_image:
            log.info('Perform auto-guiding on new image...')
        else:
            log.info('Initialising auto-guiding with new image...')

        # get image data and header
        data, hdr = image.data, image.header

        # trimsec
        if 'TRIMSEC' in hdr:
            m = re.match('\[([0-9]+):([0-9]+),([0-9]+):([0-9]+)\]', hdr['TRIMSEC'])
            x0, x1, y0, y1 = [int(f) for f in m.groups()]
            data = data[y0-1:y1, x0-1:x1]

        # collapse
        sum_x = np.nansum(data, 0)
        sum_y = np.nansum(data, 1)

        # sky subtraction
        sum_x = self._subtract_sky(sum_x)
        sum_y = self._subtract_sky(sum_y)

        # is this the new reference?
        if not self._ref_image:
            # yes, just store it
            self._reset_guiding(sum_x, sum_y, hdr)
            return

        # check RA/Dec in header and separation
        c1 = SkyCoord(ra=hdr['TEL-RA'] * u.deg, dec=hdr['TEL-DEC'] * u.deg, frame='icrs')
        c2 = SkyCoord(ra=self._ref_header['TEL-RA'] * u.deg, dec=self._ref_header['TEL-DEC'] * u.deg, frame='icrs')
        separation = c1.separation(c2).deg
        if separation * 3600. > self._separation_reset:
            log.warning('Nominal position of reference and new image differ by %.2f", resetting reference...',
                            separation * 3600.)
            self._reset_guiding(sum_x, sum_y, hdr)
            return

        # check filter
        if 'FILTER' in hdr and 'FILTER' in self._ref_header and hdr['FILTER'] != self._ref_header['FILTER']:
            log.warning('The filter has been changed since the last exposure, resetting reference...')
            self._reset_guiding(sum_x, sum_y, hdr)
            return

        # check times and focus
        if self._last_header is not None:
            # check times
            t = Time(hdr['DATE-OBS'])
            t0 = Time(self._last_header['DATE-OBS'])
            if (t - t0).sec > self._max_interval:
                log.warning('Time between current and last image is too large, resetting reference...')
                self._reset_guiding(sum_x, sum_y, hdr)
                return

            # check focus
            if abs(hdr['TEL-FOCU'] - self._last_header['TEL-FOCU']) > 0.05:
                log.warning('Focus difference between current and last image is too large, resetting reference...')
                self._reset_guiding(sum_x, sum_y, hdr)
                return

        # remember header
        self._last_header = hdr

        # find peaks
        dx = self._correlate(sum_x, self._ref_image[0])
        dy = self._correlate(sum_y, self._ref_image[1])
        if dx is None or dy is None:
            log.error('Could not correlate image with reference.')
            return
        else:
            log.info('Found pixel shift of dx=%.2f, dy=%.2f.', dx, dy)

        # get pixel in middle of image
        cx, cy = (np.array(data.shape) / 2.).astype(np.int)

        # get WCS and RA/DEC for pixel and pixel + dx/dy
        w = WCS(hdr)
        lon, lat = w.all_pix2world(cx, cy, 0)
        radec1 = SkyCoord(ra=lon * u.deg, dec=lat * u.deg, frame='icrs', obstime=t, location=location)
        lon, lat = w.all_pix2world(cx + dx, cy + dy, 0)
        radec2 = SkyCoord(ra=lon * u.deg, dec=lat * u.deg, frame='icrs', obstime=t, location=location)

        # calculate offsets
        dra = radec2.ra.degree - radec1.ra.degree
        ddec = radec2.dec.degree - radec1.dec.degree
        log.info('Transformed to RA/Dec shift of dRA=%.2f", dDec=%.2f".', dra * 3600., ddec * 3600.)

        # too large?
        max_offset = self._max_offset
        if abs(dra * 3600.) > max_offset or abs(ddec * 3600.) > max_offset:
            log.warning('Shift too large, skipping auto-guiding for now...')
            return

        # exposure time too large
        if hdr['EXPTIME'] > self._max_exposure_time:
            log.warning('Exposure time too large, skipping auto-guiding for now...')
            return

        # push offset into PID
        if self._pid:
            dra = self._pid_ra.update(dra)
            ddec = self._pid_dec.update(ddec)
            log.info('PID results in RA/Dec shift of dRA=%.2f", dDec=%.2f.', dra * 3600., ddec * 3600.)

        # is telescope on an equitorial mount?
        if isinstance(telescope, IEquitorialMount):
            # get current offset
            cur_dra, cur_ddec = telescope.get_radec_offsets().wait()

            # move offset
            log.info('Offsetting telescope...')
            telescope.set_radec_offsets(cur_dra + dra, cur_ddec + ddec).wait()
            log.info('Finished image.')
            self._loop_closed = True

        elif isinstance(telescope, IAltAzMount):
            # transform both to Alt/AZ
            altaz1 = radec1.transform_to(AltAz)
            altaz2 = radec2.transform_to(AltAz)

            # calculate offsets
            dalt = altaz2.alt.degree - altaz1.alt.degree
            daz = altaz2.az.degree - altaz1.az.degree
            log.info('Transformed to Alt/Az shift of dalt=%.2f", daz=%.2f.', dalt * 3600., daz * 3600.)

            # get current offset
            cur_dalt, cur_daz = telescope.get_altaz_offsets().wait()

            # move offset
            log.info('Offsetting telescope...')
            telescope.set_altaz_offsets(cur_dalt + dalt, cur_daz + daz).wait()
            log.info('Finished image.')
            self._loop_closed = True

        else:
            log.warning('Telescope has neither altaz nor equitorial mount. No idea how to move it...')

    def reset(self):
        """Reset auto-guider."""
        self._reset_guiding()

    def is_loop_closed(self) -> bool:
        """Whether loop is closed."""
        return self._loop_closed

    @staticmethod
    def _gaussian(pars, x):
        a = pars[0]
        x0 = pars[1]
        sigma = pars[2]
        return a * np.exp(-((x - x0) ** 2) / (2. * sigma ** 2))

    @staticmethod
    def _gaussian_fit(pars, y, x):
        err = y - AutoGuidingProjection._gaussian(pars, x)
        return (err * err).sum()

    @staticmethod
    def _correlate(data1, data2, fit_width=10):
        # do cross-correlation
        corr = np.correlate(data1, data2, "full")

        # find index of maximum
        i_max = np.argmax(corr)
        centre = i_max - data1.size + 1

        # cut window
        x = np.linspace(centre - fit_width, centre + fit_width, 2 * fit_width + 1)
        y = corr[i_max - fit_width:i_max + fit_width + 1]

        # moment calculation for initial guesses
        total = float(y.sum())
        m = (x * y).sum() / total
        m2 = (x * x * y).sum() / total - m**2

        # initial guess
        guesses = [np.max(y), m, m2]

        # perform fit
        result = fmin(AutoGuidingProjection._gaussian_fit, guesses, args=(y, x), disp=False)

        # sanity check and finish up
        shift = result[1]
        if shift < centre - fit_width or shift > centre + fit_width:
            return None
        return shift

    def _reset_guiding(self, sum_x=None, sum_y=None, hdr=None):
        # reset guiding
        self._loop_closed = False
        if sum_x is None or sum_y is None or hdr is None:
            self._ref_image = None
            self._ref_header = None
            self._last_header = None
        else:
            self._ref_image = (sum_x, sum_y)
            self._ref_header = hdr
            self._last_header = hdr
        self._init_pid()

    def _init_pid(self):
        # init pids
        Kp = 0.2
        Ki = 0.16
        Kd = 0.83

        # reset
        self._pid_ra = PID(Kp, Ki, Kd)
        self._pid_dec = PID(Kp, Ki, Kd)

    @staticmethod
    def _subtract_sky(data, frac=0.15, sbin=10):
        # find continuum for every of the sbin bins
        bins = np.zeros((sbin))
        binxs = np.zeros((sbin))
        x = list(range(len(data)))
        w1 = 0
        w2 = float(len(x)) / sbin
        for i in range(sbin):
            # sort data in range
            bindata = list(reversed(sorted(data[int(w1):int(w2)])))
            # calculate median and set wavelength
            bins[i] = np.median(bindata[int(-frac * len(bindata)):-1])
            binxs[i] = np.mean(x[int(w1):int(w2)])
            # reset ranges
            w1 = w2
            w2 += float(len(x)) / sbin
            # check for last bin
            if i == sbin - 1:
                w2 = len(x)

        # fit it
        w = np.where(~np.isnan(bins))
        ip = UnivariateSpline(binxs[w], bins[w])
        cont = ip(x)

        # return continuum
        return data - cont


__all__ = ['AutoGuidingProjection']
