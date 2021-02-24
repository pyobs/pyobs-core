import logging
from typing import Union, Tuple
import numpy as np
from astropy.coordinates import SkyCoord, AltAz
from astropy.wcs import WCS
import astropy.units as u

from pyobs.interfaces import ITelescope, ICamera, IAcquisition, IRaDecOffsets, IAltAzOffsets, ICameraExposureTime, \
    IImageType
from pyobs import Module
from pyobs.mixins import CameraSettingsMixin
from pyobs.modules import timeout
from pyobs.utils.enums import ImageType
from pyobs.images import Image
from pyobs.images.processors import SoftBin
from pyobs.utils.publisher import CsvPublisher
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class BaseAcquisition(Module, CameraSettingsMixin, IAcquisition):
    """Base class for telescope acquisition."""

    def __init__(self, telescope: Union[str, ITelescope], camera: Union[str, ICamera],
                 target_pixel: Tuple = None, attempts: int = 5, tolerance: float = 1,
                 max_offset: float = 120, log_file: str = None, soft_bin: int = None, *args, **kwargs):
        """Create a new base acquisition.

        Args:
            telescope: Name of ITelescope.
            camera: Name of ICamera.
            target_pixel: (x, y) tuple of pixel that the star should be positioned on. If None, center of image is used.
            attempts: Number of attempts before giving up.
            tolerance: Tolerance in position to reach in arcsec.
            max_offset: Maximum offset to move in arcsec.
            log_file: Name of file to write log to.
            soft_bin: Factor to the images with before processing.
        """
        Module.__init__(self, *args, **kwargs)

        # store telescope and camera
        self._telescope = telescope
        self._camera = camera

        # store
        self._target_pixel = target_pixel
        self._attempts = attempts
        self._tolerance = tolerance
        self._max_offset = max_offset

        # init log file
        self._publisher = CsvPublisher(log_file)

        # binning
        self._soft_bin = None if soft_bin is None else SoftBin(binning=soft_bin)

        # init camera settings mixin
        CameraSettingsMixin.__init__(self, *args, **kwargs)

    def open(self):
        """Open module"""
        Module.open(self)

        # check telescope and camera
        try:
            self.proxy(self._telescope, ITelescope)
            self.proxy(self._camera, ICamera)
        except ValueError:
            log.warning('Either camera or telescope do not exist or are not of correct type at the moment.')

    @timeout(300)
    def acquire_target(self, exposure_time: float, *args, **kwargs) -> dict:
        """Acquire target at given coordinates.

        If no RA/Dec are given, start from current position. Might not work for some implementations that require
        coordinates.

        Args:
            exposure_time: Exposure time for acquisition in secs.

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
            # set exposure time and image type and take image
            if isinstance(camera, ICameraExposureTime):
                log.info('Exposing image for %.1f seconds...', exposure_time)
                camera.set_exposure_time(exposure_time).wait()
            else:
                log.info('Exposing image...')
            if isinstance(camera, IImageType):
                camera.set_image_type(ImageType.ACQUISITION)
            filename = camera.expose().wait()

            # download image
            log.info('Downloading image...')
            img = self.vfs.read_image(filename)

            # bin?
            if self._soft_bin is not None:
                self._soft_bin(img)

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

            # get current position (without offsets!)
            cur_ra, cur_dec = telescope.get_radec().wait()
            radec_current = SkyCoord(ra=cur_ra * u.deg, dec=cur_dec * u.deg, frame='icrs',
                                     obstime=date_obs, location=self.location)

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
                if self._publisher is not None:
                    self._publisher(**log_entry)

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

                # calculate total offsets
                total_dra, total_ddec = float(cur_dra + dra), float(cur_ddec + ddec)

                # move offset
                log.info('Offsetting telescope to dRA=%.2f", dDec=%.2f"...', total_dra * 3600., total_ddec * 3600.)
                telescope.set_radec_offsets(total_dra, total_ddec).wait()

                # for testing, calculate offsets from current
                t1, t2 = radec_current.spherical_offsets_to(radec_target)
                log.info('TESTING: dRA=%.2f", dDec=%.2f"', t1.arcsec, t2.arcsec)

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

    def _get_target_radec(self, img: Image, ra: float, dec: float) -> Tuple[float, float]:
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
