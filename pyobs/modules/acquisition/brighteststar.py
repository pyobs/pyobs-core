import logging
from typing import Union, Tuple
import numpy as np
from astropy.coordinates import SkyCoord, AltAz
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.wcs import WCS
import astropy.units as u
from photutils import DAOStarFinder

from pyobs.interfaces import ITelescope, ICamera, IAcquisition, IEquitorialMount, IAltAzMount
from pyobs import PyObsModule
from pyobs.modules import timeout
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class BrightestStarAcquisition(PyObsModule, IAcquisition):
    """Module for acquiring telescope on brightest star in field."""

    def __init__(self, telescope: Union[str, ITelescope], camera: Union[str, ICamera],
                 target_pixel: Tuple = None, attempts: int = 5, tolerance: float = 1, *args, **kwargs):
        """Acquire on brightest star in field..

        Args:
            telescope: Name of ITelescope.
            camera: Name of ICamera.
            target_pixel: (x, y) tuple of pixel that the star should be positioned on. If None, center of image is used.
            attempts: Number of attempts before giving up.
            tolerance: Tolerance in position to reach.
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # store telescope and camera
        self._telescope = telescope
        self._camera = camera

        # store
        self._target_pixel = target_pixel
        self._attempts = attempts
        self._tolerance = tolerance

    def open(self):
        """Open module"""
        PyObsModule.open(self)

        # check telescope and camera
        try:
            self.proxy(self._telescope, ITelescope)
            self.proxy(self._camera, ICamera)
        except ValueError:
            log.warning('Either camera or telescope do not exist or are not of correct type at the moment.')

    @timeout(300000)
    def acquire_target(self, exposure_time: int, *args, **kwargs):
        """Acquire target at given coordinates.

        Args:
            exposure_time: Exposure time for acquisition.
        """

        # get focuser
        log.info('Getting proxy for focuser...')
        telescope: ITelescope = self.proxy(self._telescope, ITelescope)

        # get camera
        log.info('Getting proxy for camera...')
        camera: ICamera = self.proxy(self._camera, ICamera)

        # try given number of attempts
        for a in range(self._attempts):
            # take image
            log.info('Exposing image for %.1f seconds...', exposure_time / 1000.)
            filename = camera.expose(exposure_time, ICamera.ImageType.ACQUISITION).wait()[0]

            # download image
            log.info('Downloading image...')
            with self.open_file(filename, 'rb') as f:
                tmp = fits.open(f, memmap=False)
                img = fits.PrimaryHDU(data=tmp[0].data, header=tmp[0].header)
                tmp.close()

            # get required shift in RA/Dec
            radec1, radec2 = self._get_radec_shift(img)

            # calculate offsets and return them
            dra = radec2.ra.degree - radec1.ra.degree
            ddec = radec2.dec.degree - radec1.dec.degree
            dist = radec1.separation(radec2).degree
            log.info('Found RA/Dec shift of dRA=%.2f", dDec=%.2f", giving %.2f" in total.',
                     dra * 3600., ddec * 3600., dist * 3600.)

            # get distance
            if dist * 3600. < self._tolerance:
                # we're finished!
                log.info('Target successfully acquired.')
                return
            if dist * 3600. > 120:
                # move a maximum of 120"=2'
                log.info('Calculated offsets too large.')
                return

            # is telescope on an equitorial mount?
            if isinstance(telescope, IEquitorialMount):
                # get current offset
                cur_dra, cur_ddec = telescope.get_radec_offsets().wait()

                # move offset
                log.info('Offsetting telescope...')
                telescope.set_radec_offsets(cur_dra + dra, cur_ddec + ddec).wait()

            elif isinstance(telescope, IAltAzMount):
                # transform both to Alt/AZ
                altaz1 = radec1.transform_to(AltAz)
                altaz2 = radec2.transform_to(AltAz)

                # calculate offsets
                dalt = altaz2.alt.degree - altaz1.alt.degree
                daz = altaz2.az.degree - altaz1.az.degree
                log.info('Transformed to Alt/Az shift of dalt=%.2f", daz=%.2f".', dalt * 3600., daz * 3600.)

                # get current offset
                cur_dalt, cur_daz = telescope.get_altaz_offsets().wait()
                log.info('Current offsets alt=%.2f, az=%.2f.', cur_dalt * 3600, cur_daz * 3600)

                # move offset
                log.info('Offsetting telescope...')
                telescope.set_altaz_offsets(cur_dalt + dalt, cur_daz + daz).wait()

            else:
                log.warning('Telescope has neither altaz nor equitorial mount. No idea how to move it...')

        # could not acquire target
        raise ValueError('Could not acquire target within given tolerance.')

    def _get_radec_shift(self, img):
        # get target pixel
        if self._target_pixel is None:
            cy, cx = (np.array(img.data.shape) / 2.).astype(np.int)
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
        log.info('Found brightest star at x=%.2f, y=%.2f.', target['xcentroid'], target['ycentroid'])
        log.info('Distance to center at (%.2f, %.2f) is dx=%.2f, dy=%.2f.',
                 cx, cy, target['xcentroid'] - cx, target['ycentroid'] - cy)

        # get obs time
        time = Time(img.header['DATE-OBS'])

        # get WCS and RA/DEC for pixel and pixel + dx/dy
        w = WCS(img.header)
        lon, lat = w.all_pix2world(cx, cy, 0)
        radec_center = SkyCoord(ra=lon * u.deg, dec=lat * u.deg, frame='icrs', obstime=time, location=self.location)
        lon, lat = w.all_pix2world(target['xcentroid'], target['ycentroid'], 0)
        radec_target = SkyCoord(ra=lon * u.deg, dec=lat * u.deg, frame='icrs', obstime=time, location=self.location)
        return radec_center, radec_target


__all__ = ['BrightestStarAcquisition']
