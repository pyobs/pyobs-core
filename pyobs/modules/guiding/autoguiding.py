import logging

from pyobs.interfaces import ICamera
from .base import BaseGuiding

log = logging.getLogger(__name__)


class AutoGuiding(BaseGuiding):
    """An auto-guiding system."""

    def __init__(self, *args, **kwargs):
        """Initializes a new auto guiding system."""
        BaseGuiding.__init__(self, *args, **kwargs)

        # store
        self._exp_time = 1000

        # add thread func
        self._add_thread_func(self._auto_guiding, True)

    def set_exposure_time(self, exp_time: int):
        """Set the exposure time for the auto-guider.

        Args:
            exp_time: Exposure time in ms.
        """
        log.info('Setting exposure time to %dms...', exp_time)
        self._exp_time = exp_time
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
                log.info('Taking image with an exposure time of %dms...', self._exp_time)
                filenames = camera.expose(self._exp_time, ICamera.ImageType.OBJECT, 1, False).wait()

                # download image
                image = self.vfs.read_image(filenames[0])

                # process it
                log.info('Processing image...')
                self._process_image(image)

            except Exception as e:
                log.error('An error occurred: ', e)
                self.closing.wait(5)


__all__ = ['AutoGuiding']
