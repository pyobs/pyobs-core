from __future__ import annotations
import logging
from typing import Any, Optional, Union, TYPE_CHECKING, Tuple

from pyobs.interfaces import IBinning, ICamera, IWindow, IExposureTime, IImageType, IData, IModule
from pyobs.robotic.scripts import Script
from pyobs.utils.enums import ImageType

if TYPE_CHECKING:
    from pyobs.robotic import TaskSchedule, TaskArchive, TaskRunner

log = logging.getLogger(__name__)


class SkyflatsPointing(Script):
    """Script for setting pointing via pointing module."""

    def __init__(
        self,
        pointing: Union[str, IModule],
        **kwargs: Any,
    ):
        """Init a new DarkBias script.
        Args:

        """
        if "configuration" not in kwargs:
            kwargs["configuration"] = {}
        Script.__init__(self, **kwargs)

        # store modules
        self._pointing = pointing

    async def can_run(self) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """
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
        log.info("Setting pointing for skyflats...")
        pointing_module = await self.comm.proxy(self._pointing, IModule)
        await pointing_module.run()
        log.info("Pointing for skyflats set.")


__all__ = ["SkyflatsPointing"]
