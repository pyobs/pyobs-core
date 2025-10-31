import asyncio
import logging
from typing import Any, Optional

from pyobs.mixins import CameraSettingsMixin
from pyobs.modules import timeout
from pyobs.modules.pointing._baseguiding import BaseGuiding
from pyobs.images.meta.exptime import ExpTime
from pyobs.images.processors.detection import SepSourceDetection
from pyobs.interfaces import IExposureTime, IImageType, IData, ICamera
from pyobs.utils.enums import ImageType, ExposureStatus

log = logging.getLogger(__name__)


class AutoGuiding(BaseGuiding, CameraSettingsMixin):
    """An auto-guiding system."""

    __module__ = "pyobs.modules.guiding"

    def __init__(self, exposure_time: float = 1.0, broadcast: bool = False, **kwargs: Any):
        """Initializes a new auto guiding system.

        Args:
            exposure_time: Initial exposure time in seconds.
            broadcast: Whether to broadcast new images.
        """
        BaseGuiding.__init__(self, **kwargs)

        # store
        self._default_exposure_time = exposure_time
        self._exposure_time: Optional[float] = None
        self._broadcast = broadcast
        self._source_detection = SepSourceDetection()

        # init camera settings mixin
        CameraSettingsMixin.__init__(self, **kwargs)

        # add thread func
        self.add_background_task(self._auto_guiding)

    async def set_exposure_time(self, exposure_time: float, **kwargs: Any) -> None:
        """Set the exposure time in seconds.

        Args:
            exposure_time: Exposure time in seconds.

        Raises:
            ValueError: If exposure time could not be set.
        """
        log.info("Setting exposure time to %ds...", exposure_time)
        self._default_exposure_time = exposure_time
        self._exposure_time = None
        self._loop_closed = False
        await self._reset_guiding(enabled=self._enabled)

    async def get_exposure_time(self, **kwargs: Any) -> float:
        """Returns the exposure time in seconds.

        Returns:
            Exposure time in seconds.
        """
        return self._default_exposure_time

    async def get_exposure_time_left(self, **kwargs: Any) -> float:
        return 0.0

    async def start(self, **kwargs: Any) -> None:
        """Starts/resets auto-guiding."""
        await BaseGuiding.start(self)
        self._exposure_time = self._default_exposure_time

    @timeout(60)
    async def stop(self, **kwargs: Any) -> None:
        """Stops auto-guiding."""
        log.info("Stopping auto-guiding...")
        camera = await self.proxy(self._camera, ICamera)
        while await camera.get_exposure_status() != ExposureStatus.IDLE:
            await asyncio.sleep(1)
        await BaseGuiding.stop(self)

    async def _auto_guiding(self) -> None:
        # exposure time
        self._exposure_time = self._default_exposure_time

        # run until closed
        while True:
            # not running?
            if not self._enabled:
                await asyncio.sleep(1)
                continue

            try:
                # get camera
                camera = await self.proxy(self._camera, IData)

                # do camera settings
                await self._do_camera_settings(camera)

                # take image
                if isinstance(camera, IExposureTime):
                    # set exposure time
                    log.info("Taking image with an exposure time of %.2fs...", self._exposure_time)
                    await camera.set_exposure_time(self._exposure_time)
                else:
                    log.info("Taking image...")
                if isinstance(camera, IImageType):
                    await camera.set_image_type(ImageType.GUIDING)
                filename = await camera.grab_data(broadcast=self._broadcast)

                # download image
                image = await self.vfs.read_image(filename)

                # process it
                log.info("Processing image...")
                processed_image = await self._process_image(image)
                log.info("Done.")

                # new exposure time?
                if processed_image is not None and processed_image.has_meta(ExpTime):
                    self._exposure_time = processed_image.get_meta(ExpTime).exptime

                # sleep a little
                await asyncio.sleep(self._min_interval)

            except:
                log.exception("An error occurred: ")
                await asyncio.sleep(5)


__all__ = ["AutoGuiding"]
