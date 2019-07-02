import logging
from typing import Union, Tuple
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.wcs import WCS
import astropy.units as u
from photutils import DAOStarFinder

from pyobs.interfaces import ITelescope, ICamera, IAcquisition
from pyobs import PyObsModule
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class BrightestStarAcquisition(PyObsModule, IAcquisition):
    """Module for acquiring telescope on brightest star in field."""

    def __init__(self, telescope: Union[str, ITelescope], camera: Union[str, ICamera], exptime: int = 2000,
                 target_pixel: Tuple = None, *args, **kwargs):
        """Acquire on brightest star in field..

        Args:
            telescope: Name of ITelescope.
            camera: Name of ICamera.
            exptime: Exposure time in ms.
            target_pixel: (x, y) tuple of pixel that the star should be positioned on. If None, center of image is used.
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # store telescope and camera
        self._telescope = telescope
        self._camera = camera

        # store
        self._exptime = exptime
        self._target_pixel = target_pixel

    def open(self):
        """Open module"""
        PyObsModule.open(self)

        # check telescope and camera
        try:
            self.proxy(self._telescope, ITelescope)
            self.proxy(self._camera, ICamera)
        except ValueError:
            log.warning('Either camera or telescope do not exist or are not of correct type at the moment.')

    def acquire_target(self, ra: float, dec: float, *args, **kwargs):
        """Acquire target at given coordinates.

        Args:
            ra: Right ascension of target to acquire.
            dec: Declination of target to acquire.
        """

        # get focuser
        log.info('Getting proxy for focuser...')
        telescope: ITelescope = self.proxy(self._telescope, ITelescope)

        # get camera
        log.info('Getting proxy for camera...')
        camera: ICamera = self.proxy(self._camera, ICamera)

        # move telescope to ra/dev
        telescope.track_radec(ra, dec).wait()

        # take image
        filename = camera.expose(self._exptime, ICamera.ImageType.OBJECT, broadcast=False).wait()

        # download image
        log.info('Downloading image...')
        with self.open_file(filename, 'rb') as f:
            tmp = fits.open(f, memmap=False)
            img = fits.PrimaryHDU(data=tmp[0].data, header=tmp[0].header)
            tmp.close()

        # get required shift in RA/Dec
        dra, ddec = self._get_radec_shift(img)
        log.info('Found RA/Dec shift of dRA=%.2f", dDec=%.2f".', dra * 3600., ddec * 3600.)

    def _get_radec_shift(self, img):
        # get target pixel
        if self._target_pixel is None:
            cx, cy = (np.array(img.data.shape) / 2.).astype(np.int)
        else:
            cx, cy = self._target_pixel

        # do statistics on image
        mean, median, std = sigma_clipped_stats(img.data, sigma=3.0)

        # find stars
        daofind = DAOStarFinder(fwhm=3.0, threshold=5. * std)
        sources = daofind(img.data - median).to_pandas()

        # sort by flux
        sources.sort_values('flux', ascending=False, inplace=True)

        # target is first one in list
        target = sources.iloc[0]

        # get obs time
        time = Time(img.header['DATE-OBS'])

        # get WCS and RA/DEC for pixel and pixel + dx/dy
        w = WCS(img.header)
        lon, lat = w.all_pix2world(cx, cy, 0)
        radec_center = SkyCoord(ra=lon * u.deg, dec=lat * u.deg, frame='icrs', obstime=time, location=self.location)
        lon, lat = w.all_pix2world(target['xcentroid'], target['ycentroid'], 0)
        radec_target = SkyCoord(ra=lon * u.deg, dec=lat * u.deg, frame='icrs', obstime=time, location=self.location)

        # calculate offsets and return them
        dra = radec_target.ra.degree - radec_center.ra.degree
        ddec = radec_target.dec.degree - radec_center.dec.degree
        return dra, ddec


__all__ = ['BrightestStarAcquisition']
