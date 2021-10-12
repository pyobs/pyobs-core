import logging
from typing import Union, Tuple, List
import astropy.units as u

from pyobs.images.meta import OnSkyDistance
from pyobs.interfaces import ITelescope, ICamera, IAcquisition, IRaDecOffsets, IAltAzOffsets, IExposureTime, \
    IImageType, IImageGrabber
from pyobs.mixins.pipeline import PipelineMixin
from pyobs.modules import Module
from pyobs.mixins import CameraSettingsMixin
from pyobs.modules import timeout
from pyobs.object import get_object
from pyobs.utils.enums import ImageType
from pyobs.images import ImageProcessor
from pyobs.utils.offsets import ApplyOffsets
from pyobs.utils.publisher import CsvPublisher
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class Acquisition(Module, CameraSettingsMixin, IAcquisition, PipelineMixin):
    """Class for telescope acquisition."""
    __module__ = 'pyobs.modules.acquisition'

    def __init__(self, telescope: Union[str, ITelescope], camera: Union[str, ICamera],
                 pipeline: List[Union[dict, ImageProcessor]], apply: Union[dict, ApplyOffsets],
                 target_pixel: Tuple = None, attempts: int = 5, tolerance: float = 1,
                 max_offset: float = 120, log_file: str = None, *args, **kwargs):
        """Create a new acquisition.

        Args:
            telescope: Name of ITelescope.
            camera: Name of ICamera.
            pipeline: Pipeline steps to run on new image. MUST include a step calculating offsets!
            apply: Object that handles applying offsets to telescope.
            target_pixel: (x, y) tuple of pixel that the star should be positioned on. If None, center of image is used.
            attempts: Number of attempts before giving up.
            tolerance: Tolerance in position to reach in arcsec.
            max_offset: Maximum offset to move in arcsec.
            log_file: Name of file to write log to.
        """
        Module.__init__(self, *args, **kwargs)
        PipelineMixin.__init__(self, pipeline)

        # store telescope and camera
        self._telescope = telescope
        self._camera = camera

        # store
        self._is_running = False
        self._target_pixel = target_pixel
        self._attempts = attempts
        self._tolerance = tolerance * u.arcsec
        self._max_offset = max_offset * u.arcsec

        # init log file
        self._publisher = CsvPublisher(log_file) if log_file is not None else None

        # apply offsets
        self._apply = get_object(apply, ApplyOffsets)

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

    def is_running(self, *args, **kwargs) -> bool:
        """Whether a service is running."""
        return self._is_running

    @timeout(120)
    def acquire_target(self, exposure_time: float, *args, **kwargs) -> dict:
        """Acquire target at given coordinates.

        If no RA/Dec are given, start from current position. Might not work for some implementations that require
        coordinates.

        Args:
            exposure_time: Exposure time for acquisition in secs.

        Returns:
            A dictionary with entries for datetime, ra, dec, alt, az, and either off_ra, off_dec or off_alt, off_az.

        Raises:
            ValueError: If target could not be acquired.
        """

        try:
            self._is_running = True
            return self._acquire(exposure_time)
        finally:
            self._is_running = False

    def _acquire(self, exposure_time: float) -> dict:
        """Actually acquire target."""

        # get telescope
        log.info('Getting proxy for telescope...')
        telescope: ITelescope = self.proxy(self._telescope, ITelescope)

        # get camera
        log.info('Getting proxy for camera...')
        camera: ICamera = self.proxy(self._camera, IImageGrabber)

        # do camera settings
        self._do_camera_settings(camera)

        # try given number of attempts
        for a in range(self._attempts):
            # set exposure time and image type and take image
            if isinstance(camera, IExposureTime):
                log.info('Exposing image for %.1f seconds...', exposure_time)
                camera.set_exposure_time(exposure_time).wait()
            else:
                log.info('Exposing image...')
            if isinstance(camera, IImageType):
                camera.set_image_type(ImageType.ACQUISITION)
            filename = camera.grab_image().wait()

            # download image
            log.info('Downloading image...')
            if filename is None:
                log.warning('Did not receive an image.')
                continue
            image = self.vfs.read_image(filename)

            # get offset
            log.info('Analysing image...')
            image = self.run_pipeline(image)

            # calculate distance from offset
            dist = image.get_meta(OnSkyDistance).distance
            log.info('Found a distance to target of %.2f arcsec.', dist.arcsec)

            # get distance
            if dist < self._tolerance:
                # we're finished!
                log.info('Target successfully acquired.')

                # get current Alt/Az
                cur_alt, cur_az = telescope.get_altaz().wait()
                cur_ra, cur_dec = telescope.get_radec().wait()

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
            if dist > self._max_offset:
                # move a maximum of 120"=2'
                raise ValueError('Calculated offsets too large.')

            # get telescope
            try:
                telescope: ITelescope = self.proxy(self._telescope, ITelescope)
            except ValueError:
                log.error('Given telescope does not exist or is not of correct type.')
                continue

            # apply offsets
            if self._apply(image, telescope, self.location):
                log.info('Finished image.')
            else:
                log.warning('Could not apply offsets.')

        # could not acquire target
        raise ValueError('Could not acquire target within given tolerance.')


__all__ = ['Acquisition']
