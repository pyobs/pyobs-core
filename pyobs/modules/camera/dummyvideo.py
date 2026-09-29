from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

import numpy as np

from pyobs.interfaces import ExposureTimeState, IExposureTime
from pyobs.modules.camera.basevideo import BaseVideo
from pyobs.modules.camera.videoframes import Frame

log = logging.getLogger(__name__)


class DummyVideo(BaseVideo, IExposureTime):
    """A dummy video module for testing — streams simulated noise frames."""

    __module__ = "pyobs.modules.camera"

    def __init__(
        self,
        fps: float = 1.0,
        image_size: tuple[int, int] | None = None,
        **kwargs: Any,
    ):
        """Creates a new dummy video module.

        Args:
            fps: Frames per second to simulate.
            image_size: Size of simulated frames (width, height).
        """
        BaseVideo.__init__(self, **kwargs)
        self._fps = fps
        self._image_size = image_size if image_size is not None else (640, 480)
        self._exposure_time = 1.0 / fps

    async def open(self) -> None:
        """Open module."""
        await BaseVideo.open(self)
        await self.comm.set_state(IExposureTime, ExposureTimeState(exposure_time=self._exposure_time))

    async def set_exposure_time(self, exposure_time: float, **kwargs: Any) -> None:
        """Set the exposure time (frame interval).

        Args:
            exposure_time: Exposure time in seconds.
        """
        self._exposure_time = exposure_time
        self._fps = 1.0 / exposure_time if exposure_time > 0 else 1.0
        self._new_generation()
        await self.comm.set_state(IExposureTime, ExposureTimeState(exposure_time=exposure_time))

    async def frames(self) -> AsyncIterator[Frame]:
        """Yield simulated frames: a moving gradient plus noise, one per exposure time."""
        while True:
            # the exposure starts now and ends after one exposure time
            generation, exposure_time = self.generation, self._exposure_time
            start = time.time()
            await asyncio.sleep(exposure_time)

            # generate a simple gradient + noise frame
            w, h = self._image_size
            data = np.random.randint(1000, 5000, size=(h, w), dtype=np.uint16)
            # add a moving gradient for visual interest
            x = np.arange(w)
            gradient = (np.sin(x / w * 2 * np.pi + start) * 2000 + 3000).astype(np.uint16)
            data += gradient[np.newaxis, :]
            yield Frame(data=data, start=start, exposure_time=exposure_time, generation=generation)


__all__ = ["DummyVideo"]
