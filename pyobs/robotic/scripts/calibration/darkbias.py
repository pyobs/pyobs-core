from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyobs.interfaces import (
    IBinning,
    IData,
    IExposureTime,
    IImageType,
    IWindow,
)
from pyobs.robotic.scripts import Script
from pyobs.utils.enums import ImageType

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
    from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class DarkBiasScript(Script):
    """Script for running darks or biases."""

    camera: str
    count: int = 20
    exptime: float = 0
    binning: tuple[int, int] = (1, 1)

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """

        # we need a camera
        if not await self.comm.has_proxy(self.camera, IData):
            self._cant_run_reason = "No camera found."
            return False

        # seems alright
        self._cant_run_reason = None
        return True

    async def run(self, data: TaskData | None) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """

        image_type = ImageType.BIAS if self.exptime == 0 else ImageType.DARK

        async with self.comm.safe_proxy(self.camera, IBinning) as camera:
            if camera is not None:
                await camera.set_binning(*self.binning)

        # set full frame
        async with self.comm.safe_proxy(self.camera, IWindow) as camera:
            if camera is not None:
                cap = camera.get_capabilities(IWindow)
                if cap is not None:
                    await camera.set_window(
                        cap.full_frame_x, cap.full_frame_y, cap.full_frame_width, cap.full_frame_height
                    )

        # take image
        async with self.comm.proxy(self.camera, IExposureTime) as camera:
            await camera.set_exposure_time(self.exptime)
        async with self.comm.proxy(self.camera, IImageType) as camera:
            await camera.set_image_type(image_type)

        # image type for logger
        if self.exptime == 0:
            im_type = f"{self.count} biases"

        else:
            im_type = f"{self.count} darks ({self.exptime} s)"

        log.info("Starting a series of %s with %s...", im_type, self.camera)
        async with self.comm.proxy(self.camera, IData) as camera:
            for i in range(self.count):
                await camera.grab_data()
        log.info("Finished series of %s with %s.", im_type, self.camera)
        return

    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        """Estimate duration of the dark/bias series."""
        # TODO: get a better estimate for readout overhead
        readout = 5.0
        return self.count * (self.exptime + readout)


__all__ = ["DarkBiasScript"]
