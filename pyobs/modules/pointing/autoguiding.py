from __future__ import annotations

import asyncio
import logging
from typing import Any

from pyobs.images.meta.exptime import ExpTime
from pyobs.interfaces import ExposureTimeState, IExposure, IExposureTime
from pyobs.mixins import CameraSettingsMixin
from pyobs.modules import timeout
from pyobs.modules.pointing._baseguiding import BaseGuiding
from pyobs.modules.pointing.guidingsource import GrabDataSource, GuidingFrameSource, RawStreamSource
from pyobs.utils.enums import ExposureStatus

log = logging.getLogger(__name__)


class AutoGuiding(BaseGuiding, CameraSettingsMixin):
    """An auto-guiding system."""

    __module__ = "pyobs.modules.pointing"

    def __init__(
        self,
        exposure_time: float = 1.0,
        broadcast: bool = False,
        stream: bool | str = False,
        crop_size: int | None = None,
        settle_time: float = 0.0,
        **kwargs: Any,
    ):
        """Initializes a new auto guiding system.

        Args:
            exposure_time: Initial exposure time in seconds.
            broadcast: Whether to broadcast new images (only when grabbing images, not for streams).
            stream: Guide on a video camera's raw frame stream instead of calling grab_data(): True to
                ask the camera for the stream's VFS path, or the path itself.
            crop_size: With a stream, crop it to a box of this size (unbinned pixels) around the
                brightest star, found in a full frame whenever there is no reference image.
            settle_time: Seconds to wait after applying an offset before a frame may start exposing.
        """
        super().__init__(**kwargs)

        # store
        self._default_exposure_time = exposure_time
        self._exposure_time: float | None = None
        self._broadcast = broadcast
        self._stream = stream
        self._crop_size = crop_size
        self._settle_time = settle_time
        self._source: GuidingFrameSource | None = None

        # add thread func
        self.add_background_task(self._auto_guiding)

    async def open(self) -> None:
        """Open module."""
        await BaseGuiding.open(self)
        await self.comm.set_state(IExposureTime, ExposureTimeState(exposure_time=self._default_exposure_time))

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
        async with self.safe_proxy(self._camera, IExposure) as camera:
            # video cameras streaming frames have no exposure state to wait for
            while camera is not None:
                exp_state = camera.get_state(IExposure)
                if exp_state is None or exp_state.status == ExposureStatus.IDLE:
                    break
                await asyncio.sleep(1)

    async def _auto_guiding(self) -> None:
        # exposure time
        self._exposure_time = self._default_exposure_time

        # run until closed
        source = self._frame_source()
        try:
            while True:
                await self._auto_guiding_step(source)
        finally:
            await source.close()

    def _frame_source(self) -> GuidingFrameSource:
        """Create the image source according to config."""
        if self._source is None:
            if self._stream:
                camera = self._camera if isinstance(self._camera, str) else self._camera.name  # type: ignore[union-attr]
                path = self._stream if isinstance(self._stream, str) else None
                self._source = RawStreamSource(self, camera, path=path, crop_size=self._crop_size)
            else:
                self._source = GrabDataSource(self, self._camera, broadcast=self._broadcast)  # type: ignore[arg-type]
        return self._source

    def _not_before(self) -> float:
        """Earliest exposure start for the next image: after the last correction has settled."""
        if self._last_correction_time is None:
            return 0.0
        return self._last_correction_time + self._settle_time

    async def _auto_guiding_step(self, source: GuidingFrameSource) -> None:
        """One iteration of the guiding loop."""
        # not running? drop any open stream, so the camera can go to sleep
        if not self._enabled:
            await source.close()
            await asyncio.sleep(1)
            return

        try:
            # no reference? let the source start over too (e.g. find a new guide star)
            if self._ref_header is None:
                await source.reset()

            # get image
            image = await source.next_image(self._exposure_time, self._not_before())

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
