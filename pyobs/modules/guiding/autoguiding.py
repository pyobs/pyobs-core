import logging

from pyobs.interfaces import ICamera, IImageType, ICameraExposureTime
from .base import BaseGuiding
from ...utils.enums import ImageType

log = logging.getLogger(__name__)


class AutoGuiding(BaseGuiding):
    """An auto-guiding system."""

    def __init__(self, *args, **kwargs):
        """Initializes a new auto guiding system."""
        BaseGuiding.__init__(self, *args, **kwargs)

        # store
        self._exp_time = 1.

        # add thread func
        self._add_thread_func(self._auto_guiding, True)

    def set_exposure_time(self, exposure_time: float, *args, **kwargs):
        """Set the exposure time for the auto-guider.

        Args:
            exposure_time: Exposure time in secs.
        """
        log.info('Setting exposure time to %ds...', exposure_time)
        self._exp_time = exposure_time
        self._loop_closed = False
        self._guiding_offset.reset()

    def _auto_guiding(self):
        # run until closed
        while not self.closing.is_set():
            # not running?
            if not self._enabled:
                self.closing.wait(1)
                continue

            try:
                # get camera
                camera: ICamera = self.proxy(self._camera, ICamera)

                # take image
                if isinstance(camera, ICameraExposureTime):
                    log.info('Taking image with an exposure time of %dms...', self._exp_time)
                    camera.set_exposure_time(self._exp_time)
                else:
                    log.info('Taking image...')
                if isinstance(camera, IImageType):
                    camera.set_image_type(ImageType.OBJECT)
                filename = camera.expose(broadcast=False).wait()

                # download image
                image = self.vfs.read_image(filename)

                # process it
                log.info('Processing image...')
                self._process_image(image)

            except Exception as e:
                log.error('An error occurred: ', e)
                self.closing.wait(5)


__all__ = ['AutoGuiding']
