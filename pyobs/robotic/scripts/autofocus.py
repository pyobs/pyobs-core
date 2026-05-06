from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from pyobs.interfaces import IBinning, ICamera, IWindow, IExposureTime, IImageType, IData, IAutoFocus
from pyobs.robotic.scripts import Script
from pyobs.utils.enums import ImageType

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData

log = logging.getLogger(__name__)


class AutoFocus(Script):
    """Script for running autofocus series."""

    autofocus: str

    async def can_run(self, data: TaskData) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """

        # we need a camera
        try:
            await Script._comm(data).proxy(self.autofocus, IAutoFocus)
        except ValueError:
            return False

        # seems alright
        return True

    async def run(self, data: TaskData) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """

        return


__all__ = ["AutoFocus"]
