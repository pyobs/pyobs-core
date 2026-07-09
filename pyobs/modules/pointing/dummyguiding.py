from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

from pyobs.interfaces import GuidingState, IAutoGuiding, IExposureTime, IRunning, OffsetFrame
from pyobs.interfaces.IExposureTime import ExposureTimeState
from pyobs.interfaces.IRunning import RunningState
from pyobs.modules import Module

log = logging.getLogger(__name__)


class DummyAutoGuiding(Module, IAutoGuiding):
    """An auto-guiding system."""

    __module__ = "pyobs.modules.guiding"

    def __init__(self, exposure_time: float = 1.0, interval: float = 2.0, **kwargs: Any):
        """Create a new dummy auto-guiding system.

        Args:
            exposure_time: Initial exposure time, in seconds.
            interval: Time between simulated guide corrections, in seconds.
        """
        Module.__init__(self, **kwargs)

        self._running = False
        self._exposure_time = exposure_time
        self._interval = interval
        self._last_offset: tuple[float, float] | None = None  # (lon, lat) in degrees

        self.add_background_task(self._guide_loop)

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)
        await self.comm.set_state(IExposureTime, ExposureTimeState(exposure_time=self._exposure_time))
        await self.comm.set_state(IRunning, RunningState(running=False))
        await self.comm.set_state(IAutoGuiding, GuidingState())

    async def set_exposure_time(self, exposure_time: float, **kwargs: Any) -> None:
        self._exposure_time = exposure_time
        await self.comm.set_state(IExposureTime, ExposureTimeState(exposure_time=exposure_time))

    async def start(self, **kwargs: Any) -> None:
        log.info("Start guiding.")
        self._running = True
        await self.comm.set_state(IRunning, RunningState(running=True))

    async def stop(self, **kwargs: Any) -> None:
        log.info("Stop guiding.")
        self._running = False
        await self.comm.set_state(IRunning, RunningState(running=False))
        await self._publish_guiding_state(loop_closed=False)

    async def is_running(self, **kwargs: Any) -> bool:
        return self._running

    async def _publish_guiding_state(self, loop_closed: bool) -> None:
        await self.comm.set_state(
            IAutoGuiding,
            GuidingState(
                loop_closed=loop_closed,
                offset_frame=OffsetFrame.RA_DEC if self._last_offset is not None else None,
                offset_lon=self._last_offset[0] if self._last_offset is not None else None,
                offset_lat=self._last_offset[1] if self._last_offset is not None else None,
            ),
        )

    async def _guide_loop(self) -> None:
        """Simulates periodic guide corrections while running."""
        while True:
            await asyncio.sleep(self._interval)

            if not self._running:
                continue

            # occasionally simulate a lost guide star (open loop); offsets are a ~1 arcsec-stddev
            # correction in degrees, matching the scale of a real ApplyOffsets-computed delta
            loop_closed = random.random() > 0.1
            if loop_closed:
                self._last_offset = (random.gauss(0.0, 1.0 / 3600), random.gauss(0.0, 1.0 / 3600))
            await self._publish_guiding_state(loop_closed)


__all__ = ["DummyAutoGuiding"]
