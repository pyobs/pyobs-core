from __future__ import annotations

import asyncio
import logging
from typing import Any

from pyobs.images.meta.exptime import ExpTime
from pyobs.images.processors.detection import SepSourceDetection
from pyobs.interfaces import ExposureTimeState, IData, IExposure, IExposureTime, IImageType
from pyobs.mixins import CameraSettingsMixin
from pyobs.modules import timeout
from pyobs.modules.pointing._baseguiding import BaseGuiding
from pyobs.utils.enums import ExposureStatus, ImageType

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
        self._exposure_time: float | None = None
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
        await self.comm.set_state(IExposureTime, ExposureTimeState(exposure_time=exposure_time))

    async def start(self, **kwargs: Any) -> None:
        """Starts/resets auto-guiding."""
        await BaseGuiding.start(self)
        self._exposure_time = self._default_exposure_time

    @timeout(60)
    async def stop(self, **kwargs: Any) -> None:
        """Stops auto-guiding."""
        log.info("Stopping auto-guiding...")
        await BaseGuiding.stop(self)
        async with self.proxy(self._camera, IExposure) as camera:
            while True:
                exp_state = camera.get_state(IExposure)
                if exp_state is None or exp_state.status == ExposureStatus.IDLE:
                    break
                await asyncio.sleep(1)

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
                # do camera settings
                async with self.proxy(self._camera, IData) as camera:
                    await self._do_camera_settings(camera)

                # take image
                async with self.safe_proxy(self._camera, IExposureTime) as camera:
                    if camera:
                        # set exposure time
                        log.info("Taking image with an exposure time of %.2fs...", self._exposure_time)
                        await camera.set_exposure_time(self._exposure_time)
                    else:
                        log.info("Taking image...")
                async with self.safe_proxy(self._camera, IImageType) as camera:
                    if camera:
                        await camera.set_image_type(ImageType.GUIDING)
                async with self.proxy(self._camera, IData) as camera:
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

            except Exception:
                log.exception("An error occurred: ")
                await asyncio.sleep(5)


__all__ = ["AutoGuiding"]
