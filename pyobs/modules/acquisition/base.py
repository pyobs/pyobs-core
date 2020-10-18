import logging
from typing import Union, Tuple
import numpy as np
from astropy.coordinates import SkyCoord, AltAz
from astropy.wcs import WCS
import astropy.units as u

from pyobs.interfaces import ITelescope, ICamera, IAcquisition, IRaDecOffsets, IAltAzOffsets
from pyobs import PyObsModule
from pyobs.mixins import TableStorageMixin, CameraSettingsMixin
from pyobs.modules import timeout
from pyobs.utils.images import Image
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class BaseAcquisition(PyObsModule, TableStorageMixin, CameraSettingsMixin, IAcquisition):
    """Base class for telescope acquisition."""

    def __init__(self, telescope: Union[str, ITelescope], camera: Union[str, ICamera],
                 target_pixel: Tuple = None, attempts: int = 5, tolerance: float = 1,
                 max_offset: float = 120, log_file: str = None, *args, **kwargs):
        """Create a new base acquisition.

        Args:
            telescope: Name of ITelescope.
            camera: Name of ICamera.
            target_pixel: (x, y) tuple of pixel that the star should be positioned on. If None, center of image is used.
            attempts: Number of attempts before giving up.
            tolerance: Tolerance in position to reach in arcsec.
            max_offset: Maximum offset to move in arcsec.
            log_file: Name of file to write log to.
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # store telescope and camera
        self._telescope = telescope
        self._camera = camera

        # store
        self._target_pixel = target_pixel
        self._attempts = attempts
        self._tolerance = tolerance
        self._max_offset = max_offset

        # columns for storage
        storage_columns = {
            'datetime': str,
            'ra': float,
            'dec': float,
            'alt': float,
            'az': float,
            'off_ra': float,
            'off_dec': float,
            'off_alt': float,
            'off_az': float
        }

        # init table storage and load measurements
        TableStorageMixin.__init__(self, filename=log_file, columns=storage_columns, reload_always=True)

        # init camera settings mixin
        CameraSettingsMixin.__init__(self, *args, **kwargs)

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
    def acquire_target(self, exposure_time: int, *args, **kwargs) -> dict:
        """Acquire target at given coordinates.

        If no RA/Dec are given, start from current position. Might not work for some implementations that require
        coordinates.

        Args:
            exposure_time: Exposure time for acquisition.

        Returns:
            A dictionary with entries for datetime, ra, dec, alt, az, and either off_ra, off_dec or off_alt, off_az.

        Raises:
            ValueError if target could not be acquired.
        """

        # get telescope
        log.info('Getting proxy for telescope...')
        telescope: ITelescope = self.proxy(self._telescope, ITelescope)

        # get camera
        log.info('Getting proxy for camera...')
        camera: ICamera = self.proxy(self._camera, ICamera)

        # do camera settings
        self._do_camera_settings(camera)

        # try given number of attempts
        for a in range(self._attempts):
            # take image
            log.info('Exposing image for %.1f seconds...', exposure_time / 1000.)
            filename = camera.expose(exposure_time, ICamera.ImageType.ACQUISITION).wait()[0]

            # download image
            log.info('Downloading image...')
            img = self.vfs.download_image(filename)

            # get target pixel
            if self._target_pixel is None:
                cy, cx = (np.array(img.data.shape) / 2.).astype(np.int)
            else:
                cx, cy = self._target_pixel

            # get date obs and wcc
            date_obs = Time(img.header['DATE-OBS'])
            wcs = WCS(img.header)

            # coordinates without offset
            ra, dec = img.header['CRVAL1'], img.header['CRVAL2']

            # get WCS and RA/DEC for target pixel and
            lon, lat = wcs.all_pix2world(cx, cy, 0)
            radec_center = SkyCoord(ra=lon * u.deg, dec=lat * u.deg, frame='icrs', obstime=date_obs,
                                    location=self.location)

            # get required shift in RA/Dec
            log.info('Analyzing image...')
            x_target, y_target = self._get_target_radec(img, ra, dec)

            # convert to world
            ra_target, dec_target = wcs.all_pix2world(x_target, y_target, 0)
            radec_target = SkyCoord(ra=ra_target * u.deg, dec=dec_target * u.deg, frame='icrs',
                                    obstime=date_obs, location=self.location)

            # get current position
            cur_ra, cur_dec = telescope.get_radec().wait()

            # calculate offsets and return them
            dra = (radec_target.ra.degree - radec_center.ra.degree) * np.cos(np.radians(cur_dec))
            ddec = radec_target.dec.degree - radec_center.dec.degree
            dist = radec_center.separation(radec_target).degree
            log.info('Found RA/Dec shift of dRA=%.2f", dDec=%.2f", giving %.2f" in total.',
                     dra * 3600., ddec * 3600., dist * 3600.)

            # get distance
            if dist * 3600. < self._tolerance:
                # we're finished!
                log.info('Target successfully acquired.')

                # get current Alt/Az
                cur_alt, cur_az = telescope.get_altaz().wait()

                # prepare log entry
                log_entry = {
                    'datetime': Time.now().isot,
                    'ra': cur_ra,
                    'dec': cur_dec,
                    'alt': cur_alt,
                    'az': cur_az
                }

                # Alt/Az or RA/Dec?
                if isinstance(telescope, IRaDecOffsets):
                    log_entry['off_ra'], log_entry['off_dec'] = telescope.get_radec_offsets().wait()
                elif isinstance(telescope, IAltAzOffsets):
                    log_entry['off_alt'], log_entry['off_az'] = telescope.get_altaz_offsets().wait()

                # write log
                self._append_to_table_storage(**log_entry)

                # finished
                return log_entry

            # abort?
            if dist * 3600. > self._max_offset:
                # move a maximum of 120"=2'
                raise ValueError('Calculated offsets too large.')

            # is telescope on an equitorial mount?
            if isinstance(telescope, IRaDecOffsets):
                # get current offset
                cur_dra, cur_ddec = telescope.get_radec_offsets().wait()

                # move offset
                log.info('Offsetting telescope...')
                telescope.set_radec_offsets(float(cur_dra + dra), float(cur_ddec + ddec)).wait()

            elif isinstance(telescope, IAltAzOffsets):
                # transform both to Alt/AZ
                altaz1 = radec_center.transform_to(AltAz)
                altaz2 = radec_target.transform_to(AltAz)

                # calculate offsets
                dalt = altaz2.alt.degree - altaz1.alt.degree
                daz = altaz2.az.degree - altaz1.az.degree
                log.info('Transformed to Alt/Az shift of dalt=%.2f", daz=%.2f".', dalt * 3600., daz * 3600.)

                # get current offset
                cur_dalt, cur_daz = telescope.get_altaz_offsets().wait()
                log.info('Current offsets alt=%.2f, az=%.2f.', cur_dalt * 3600, cur_daz * 3600)

                # move offset
                log.info('Offsetting telescope...')
                telescope.set_altaz_offsets(float(cur_dalt + dalt), float(cur_daz + daz)).wait()

            else:
                log.warning('Telescope has neither altaz nor equitorial mount. No idea how to move it...')

        # could not acquire target
        raise ValueError('Could not acquire target within given tolerance.')

    def _get_target_radec(self, img: Image, ra: float, dec: float) -> (float, float):
        """Returns RA/Dec coordinates of pixel that needs to be centered.

        Params:
            img: Image to analyze.
            ra: Requested RA.
            dec: Requested Declination.

        Returns:
            (ra, dec) of pixel that needs to be moved to the centre of the image.

        Raises:
            ValueError if target coordinates could not be determined.
        """
        raise NotImplemented


__all__ = ['BaseAcquisition']
