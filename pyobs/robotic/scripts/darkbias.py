from __future__ import annotations
import logging
from typing import Any, Optional, Union, TYPE_CHECKING, Tuple

from pyobs.interfaces import IBinning, ICamera, IWindow, IExposureTime, IImageType, IData
from pyobs.robotic.scripts import Script
from pyobs.utils.enums import ImageType

if TYPE_CHECKING:
    from pyobs.robotic import TaskSchedule, TaskArchive, TaskRunner

log = logging.getLogger(__name__)


class DarkBias(Script):
    """Script for running darks or biases."""

    def __init__(
        self,
        camera: Union[str, ICamera],
        count: int = 20,
        exptime: float = 0,
        binning: Tuple[int, int] = (1, 1),
        **kwargs: Any,
    ):
        """Init a new DarkBias script.
        Args:
            camera: name of ICamera that takes the dark or bias
            count: aimed number of darks or biases
            exptime: exposure time [s], exptime=0 -> Bias
            binning: binning for dark or bias
        """
        if "configuration" not in kwargs:
            kwargs["configuration"] = {}
        Script.__init__(self, **kwargs)

        # store modules
        self._camera = camera

        # stuff
        self._count = count
        self._binning = binning
        self._exptime = exptime

        if self._exptime == 0:
            self._ImageType = ImageType.BIAS
        else:
            self._ImageType = ImageType.DARK

    async def can_run(self) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """

        # we need a camera
        try:
            await self.comm.proxy(self._camera, IData)
        except ValueError:
            return False

        # seems alright
        return True

    async def run(
        self,
        task_runner: TaskRunner,
        task_schedule: Optional[TaskSchedule] = None,
        task_archive: Optional[TaskArchive] = None,
    ) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """
        # get modules
        camera = await self.comm.proxy(self._camera, ICamera)

        if isinstance(camera, IBinning):
            await camera.set_binning(*self._binning)

        # set full frame
        if isinstance(camera, IWindow):
            full_frame = await camera.get_full_frame()
            await camera.set_window(*full_frame)

        # take image
        if isinstance(camera, IExposureTime):
            await camera.set_exposure_time(self._exptime)
        if isinstance(camera, IImageType):
            await camera.set_image_type(self._ImageType)

        # image type for logger
        if self._exptime == 0:
            im_type = "%d biases" % self._count

        else:
            im_type = "%d darks (%d s)" % (self._count, self._exptime)

        log.info("Starting a series of %s with %s..." % (im_type, self._camera))
        for i in range(self._count):
            await camera.grab_data()
        log.info("Finished series of %s with %s." % (im_type, self._camera))
        return


__all__ = ["DarkBias"]
