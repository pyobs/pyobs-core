import datetime
import logging
import math
from typing import Tuple, Optional, Dict, Any
import numpy as np
from astropy.io import fits
import astropy.units as u

from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time
from pyobs.modules import Module

log = logging.getLogger(__name__)


class BaseCam(Module):
    """Base class for all camera modules."""
    __module__ = 'pyobs.modules.camera'

    def __init__(self, fits_headers: Optional[Dict[str, Any]] = None, centre: Optional[Tuple[float, float]] = None,
                 rotation: float = 0., flip: bool = False,
                 filenames: str = '/cache/pyobs-{DAY-OBS|date:}-{FRAMENUM|string:04d}-{IMAGETYP|type}00.fits.gz',
                 *args, **kwargs):
        """Creates a new BaseCamera.

        Args:
            fits_headers: Additional FITS headers.
            centre: (x, y) tuple of camera centre.
            rotation: Rotation east of north.
            flip: Whether or not to flip the image along its first axis.
            filenames: Template for file naming.
            fits_namespaces: List of namespaces for FITS headers that this camera should request
        """
        Module.__init__(self, *args, **kwargs)

        # check
        if self.comm is None:
            log.warning('No comm module given, will not be able to signal new images!')

        # store
        self._fits_headers = fits_headers if fits_headers is not None else {}
        if 'OBSERVER' not in self._fits_headers:
            self._fits_headers['OBSERVER'] = ['pyobs', 'Name of observer']
        self._centre = centre
        self._rotation = rotation
        self._flip = flip
        self._filenames = filenames
        self._exposure_time: float = 0.

        # night exposure number
        self._cache = '/pyobs/modules/%s/cache.yaml' % self.name()
        self._frame_num = 0

    def set_exposure_time(self, exposure_time: float, *args, **kwargs):
        """Set the exposure time in seconds.

        Args:
            exposure_time: Exposure time in seconds.

        Raises:
            ValueError: If exposure time could not be set.
        """
        log.info('Setting exposure time to %.5fs...', exposure_time)
        self._exposure_time = exposure_time

    def get_exposure_time(self, *args, **kwargs) -> float:
        """Returns the exposure time in seconds.

        Returns:
            Exposure time in seconds.
        """
        return self._exposure_time

    def _add_fits_headers(self, hdr: fits.Header):
        """Add FITS header keywords to the given FITS header.

        Args:
            hdr: FITS header to add keywords to.
        """

        # convenience function to return value of keyword
        def v(k):
            return hdr[k][0] if isinstance(k, list) or isinstance(k, tuple) else hdr[k]

        # we definitely need a DATE-OBS and IMAGETYP!!
        if 'DATE-OBS' not in hdr:
            log.warning('No DATE-OBS found in FITS header, adding NO further information!')
            return
        if 'IMAGETYP' not in hdr:
            log.warning('No IMAGETYP found in FITS header, adding NO further information!')
            return

        # get date obs
        date_obs = Time(hdr['DATE-OBS'])

        # UT1-UTC
        hdr['UT1_UTC'] = (float(date_obs.delta_ut1_utc), 'UT1-UTC')

        # basic stuff
        hdr['EQUINOX'] = (2000., 'Equinox of celestial coordinate system')

        # pixel size in world coordinates
        if 'DET-PIXL' in hdr and 'TEL-FOCL' in hdr and 'DET-BIN1' in hdr and 'DET-BIN2' in hdr:
            tmp = 360. / (2. * math.pi) * v('DET-PIXL') / v('TEL-FOCL')
            hdr['CDELT1'] = (-tmp * v('DET-BIN1'), 'Coordinate increment on x-axis [deg/px]')
            hdr['CDELT2'] = (+tmp * v('DET-BIN2'), 'Coordinate increment on y-axis [deg/px]')
            hdr['CUNIT1'] = ('deg', 'Units of CRVAL1, CDELT1')
            hdr['CUNIT2'] = ('deg', 'Units of CRVAL2, CDELT2')
            hdr['WCSAXES'] = (2, 'Number of WCS axes')
        else:
            log.warning('Could not calculate CDELT1/CDELT2 (DET-PIXL/TEL-FOCL/DET-BIN1/DET-BIN2 missing).')

        # do we have a location?
        if self.location is not None:
            loc = self.location
            # add location of telescope
            hdr['LONGITUD'] = (float(loc.lon.degree), 'Longitude of the telescope [deg E]')
            hdr['LATITUDE'] = (float(loc.lat.degree), 'Latitude of the telescope [deg N]')
            hdr['HEIGHT'] = (float(loc.height.value), 'Altitude of the telescope [m]')

            # add local sidereal time
            if self.observer is not None:
                lst = self.observer.local_sidereal_time(date_obs)
                hdr['LST'] = (lst.to_string(unit=u.hour, sep=':'), 'Local sidereal time')

        # date of night this observation is in
        hdr['DAY-OBS'] = (date_obs.night_obs(self.observer).strftime('%Y-%m-%d'), 'Night of observation')

        # centre pixel
        if self._centre is not None:
            hdr['DET-CPX1'] = (self._centre[0], 'x-pixel on mechanical axis in unbinned image')
            hdr['DET-CPX2'] = (self._centre[1], 'y-pixel on mechanical axis in unbinned image')
        else:
            log.warning('Could not calculate DET-CPX1/DET-CPX2 (centre not given in config).')

        # reference pixel in binned image
        if 'DET-CPX1' in hdr and 'DET-BIN1' in hdr and 'DET-CPX2' in hdr and 'DET-BIN2' in hdr:
            # offset?
            off_x, off_y = 0, 0
            if 'XORGSUBF' in hdr and 'YORGSUBF' in hdr:
                off_x = v('XORGSUBF') if 'XORGSUBF' in hdr else 0.
                off_y = v('YORGSUBF') if 'YORGSUBF' in hdr else 0.
            hdr['CRPIX1'] = ((v('DET-CPX1') - off_x) / v('DET-BIN1'), 'Reference x-pixel position in binned image')
            hdr['CRPIX2'] = ((v('DET-CPX2') - off_y) / v('DET-BIN2'), 'Reference y-pixel position in binned image')
        else:
            log.warning('Could not calculate CRPIX1/CRPIX2 '
                            '(XORGSUBF/YORGSUBF/DET-CPX1/TEL-CPX2/DET-BIN1/DET-BIN2) missing.')
        # only add all this stuff for OBJECT images
        if hdr['IMAGETYP'] not in ['dark', 'bias']:
            # projection
            hdr['CTYPE1'] = ('RA---TAN', 'RA in tangent plane projection')
            hdr['CTYPE2'] = ('DEC--TAN', 'Dec in tangent plane projection')

            # PC matrix: rotation only, shift comes from CDELT1/2
            if self._rotation is not None:
                theta_rad = math.radians(self._rotation)
                cos_theta = math.cos(theta_rad)
                sin_theta = math.sin(theta_rad)
                hdr['PC1_1'] = (+cos_theta, 'Partial of first axis coordinate w.r.t. x')
                hdr['PC1_2'] = (-sin_theta, 'Partial of first axis coordinate w.r.t. y')
                hdr['PC2_1'] = (+sin_theta, 'Partial of second axis coordinate w.r.t. x')
                hdr['PC2_2'] = (+cos_theta, 'Partial of second axis coordinate w.r.t. y')
            else:
                log.warning('Could not calculate CD matrix (rotation or CDELT1/CDELT2 missing.')

        # add FRAMENUM
        self._add_framenum(hdr)

    def _add_framenum(self, hdr: fits.Header):
        """Add FRAMENUM keyword to header

        Args:
            hdr: Header to read from and write into.
        """

        # get night from header
        night = hdr['DAY-OBS']

        # increase night exp
        self._frame_num += 1

        # do we have a cache?
        if self._cache is not None:
            # try to load it
            try:
                # load cache
                cache = self.vfs.read_yaml(self._cache)

                # get new number
                if cache is not None and 'framenum' in cache:
                    self._frame_num = cache['framenum'] + 1

                # if nights differ, reset count
                if cache is not None and 'night' in cache and night != cache['night']:
                    self._frame_num = 1

            except (FileNotFoundError, ValueError):
                pass

            # write file
            try:
                self.vfs.write_yaml({'night': night, 'framenum': self._frame_num}, self._cache)
            except (FileNotFoundError, ValueError):
                log.warning('Could not write camera cache file.')

        # set it
        hdr['FRAMENUM'] = self._frame_num

    @staticmethod
    def set_biassec_trimsec(hdr: fits.Header, left: int, top: int, width: int, height: int):
        """Calculates and sets the BIASSEC and TRIMSEC areas.

        Args:
            hdr:    FITS header (in/out)
            left:   left edge of data area
            top:    top edge of data area
            width:  width of data area
            height: height of data area
        """

        # get image area in unbinned coordinates
        img_left = hdr['XORGSUBF']
        img_top = hdr['YORGSUBF']
        img_width = hdr['NAXIS1'] * hdr['XBINNING']
        img_height = hdr['NAXIS2'] * hdr['YBINNING']

        # get intersection
        is_left = max(left, img_left)
        is_right = min(left+width, img_left+img_width)
        is_top = max(top, img_top)
        is_bottom = min(top+height, img_top+img_height)

        # for simplicity we allow prescan/overscan only in one dimension
        if (left < is_left or left+width > is_right) and (top < is_top or top+height > is_bottom):
            log.warning('BIASSEC/TRIMSEC can only be calculated with a prescan/overscan on one axis only.')
            return False

        # comments
        c1 = 'Bias overscan area [x1:x2,y1:y2] (binned)'
        c2 = 'Image area [x1:x2,y1:y2] (binned)'

        # rectangle empty?
        if is_right <= is_left or is_bottom <= is_top:
            # easy case, all is BIASSEC, no TRIMSEC at all
            hdr['BIASSEC'] = ('[1:%d,1:%d]' % (hdr['NAXIS1'], hdr['NAXIS2']), c1)
            return

        # we got a TRIMSEC, calculate its binned and windowd coordinates
        is_left_binned = np.floor((is_left - hdr['XORGSUBF']) / hdr['XBINNING']) + 1
        is_right_binned = np.ceil((is_right - hdr['XORGSUBF']) / hdr['XBINNING'])
        is_top_binned = np.floor((is_top - hdr['YORGSUBF']) / hdr['YBINNING']) + 1
        is_bottom_binned = np.ceil((is_bottom - hdr['YORGSUBF']) / hdr['YBINNING'])

        # set it
        hdr['TRIMSEC'] = ('[%d:%d,%d:%d]' % (is_left_binned, is_right_binned, is_top_binned, is_bottom_binned), c2)
        hdr['DATASEC'] = ('[%d:%d,%d:%d]' % (is_left_binned, is_right_binned, is_top_binned, is_bottom_binned), c2)

        # now get BIASSEC -- whatever we do, we only take the last (!) one
        # which axis?
        if img_left+img_width > left+width:
            left_binned = np.floor((is_right - hdr['XORGSUBF']) / hdr['XBINNING']) + 1
            hdr['BIASSEC'] = ('[%d:%d,1:%d]' % (left_binned, hdr['NAXIS1'], hdr['NAXIS2']), c1)
        elif img_left < left:
            right_binned = np.ceil((is_left - hdr['XORGSUBF']) / hdr['XBINNING'])
            hdr['BIASSEC'] = ('[1:%d,1:%d]' % (right_binned, hdr['NAXIS2']), c1)
        elif img_top+img_height > top+height:
            top_binned = np.floor((is_bottom - hdr['YORGSUBF']) / hdr['YBINNING']) + 1
            hdr['BIASSEC'] = ('[1:%d,%d:%d]' % (hdr['NAXIS1'], top_binned, hdr['NAXIS2']), c1)
        elif img_top < top:
            bottom_binned = np.ceil((is_top - hdr['YORGSUBF']) / hdr['YBINNING'])
            hdr['BIASSEC'] = ('[1:%d,1:%d]' % (hdr['NAXIS1'], bottom_binned), c1)


__all__ = ['BaseCam']
