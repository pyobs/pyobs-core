import logging
from typing import Any, Optional

from pyobs.modules.pointing._baseguiding import BaseGuiding
from pyobs.images.meta.exptime import ExpTime
from pyobs.images.processors.detection import SepSourceDetection
from pyobs.interfaces import IExposureTimeProxy, IImageTypeProxy, IImageGrabberProxy
from pyobs.utils.enums import ImageType
from pyobs.utils.parallel import event_wait

log = logging.getLogger(__name__)


class AutoGuiding(BaseGuiding):
    """An auto-guiding system."""
    __module__ = 'pyobs.modules.guiding'

    def __init__(self, exposure_time: float = 1., **kwargs: Any):
        """Initializes a new auto guiding system.

        Args:
            exposure_time: Initial exposure time in seconds.
        """
        BaseGuiding.__init__(self, **kwargs)

        # store
        self._default_exposure_time = exposure_time
        self._exposure_time: Optional[float] = None
        self._source_detection = SepSourceDetection()

        # add thread func
        self.add_background_task(self._auto_guiding)

    async def set_exposure_time(self, exposure_time: float, **kwargs: Any) -> None:
        """Set the exposure time for the auto-guider.

        Args:
            exposure_time: Exposure time in secs.
        """
        log.info('Setting exposure time to %ds...', exposure_time)
        self._default_exposure_time = exposure_time
        self._exposure_time = None
        self._loop_closed = False
        self._reset_guiding(enabled=self._enabled)

    async def _auto_guiding(self) -> None:
        # exposure time
        self._exposure_time = self._default_exposure_time

        # run until closed
        while not self.closing.is_set():
            # not running?
            if not self._enabled:
                await event_wait(self.closing, 1)
                continue

            try:
                # get camera
                camera: IImageGrabberProxy = self.proxy(self._camera, IImageGrabberProxy)

                # take image
                if isinstance(camera, IExposureTimeProxy):
                    # set exposure time
                    log.info('Taking image with an exposure time of %.2fs...', self._exposure_time)
                    await camera.set_exposure_time(self._exposure_time)
                else:
                    log.info('Taking image...')
                if isinstance(camera, IImageTypeProxy):
                    await camera.set_image_type(ImageType.OBJECT)
                filename = await camera.grab_image(broadcast=False)

                # download image
                image = await self.vfs.read_image(filename)

                # process it
                log.info('Processing image...')
                processed_image = self._process_image(image)
                log.info('Done.')

                # new exposure time?
                if processed_image is not None and processed_image.has_meta(ExpTime):
                    self._exposure_time = processed_image.get_meta(ExpTime).exptime

                # sleep a little
                await event_wait(self.closing, self._min_interval)

            except Exception as e:
                log.error('An error occurred: ', e)
                await event_wait(self.closing, 5)


__all__ = ['AutoGuiding']
