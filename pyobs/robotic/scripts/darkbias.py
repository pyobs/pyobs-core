from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from pyobs.interfaces import IBinning, ICamera, IWindow, IExposureTime, IImageType, IData
from pyobs.robotic.scripts import Script
from pyobs.utils.enums import ImageType

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData

log = logging.getLogger(__name__)


class DarkBias(Script):
    """Script for running darks or biases."""

    camera: str
    count: int = 20
    exptime: float = 0
    binning: tuple[int, int] = (1, 1)

    async def can_run(self, data: TaskData) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """

        # we need a camera
        try:
            await self.__comm(data).proxy(self.camera, IData)
        except ValueError:
            return False

        # seems alright
        return True

    async def run(self, data: TaskData) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """

        image_type = ImageType.BIAS if self.exptime == 0 else ImageType.DARK

        # get modules
        camera = await self.__comm(data).proxy(self.camera, ICamera)

        if isinstance(camera, IBinning):
            await camera.set_binning(*self.binning)

        # set full frame
        if isinstance(camera, IWindow):
            full_frame = await camera.get_full_frame()
            await camera.set_window(*full_frame)

        # take image
        if isinstance(camera, IExposureTime):
            await camera.set_exposure_time(self.exptime)
        if isinstance(camera, IImageType):
            await camera.set_image_type(image_type)

        # image type for logger
        if self.exptime == 0:
            im_type = "%d biases" % self.count

        else:
            im_type = "%d darks (%d s)" % (self.count, self.exptime)

        log.info("Starting a series of %s with %s..." % (im_type, self.camera))
        for i in range(self.count):
            await camera.grab_data()
        log.info("Finished series of %s with %s." % (im_type, self.camera))
        return


__all__ = ["DarkBias"]
