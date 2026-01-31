from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from pyobs.interfaces.IMode import IMode
from pyobs.robotic.scripts import Script
from pyobs.utils.enums import MotionStatus

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData

log = logging.getLogger(__name__)


class SelectorScript(Script):
    """Script for running Mode Selection."""

    mode: str
    selector: str

    async def can_run(self, data: TaskData) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """
        # check if selector is ready
        selector = await self.__comm(data).proxy(self.selector, IMode)
        status = await selector.get_motion_status()
        if status == MotionStatus.PARKED or status == MotionStatus.POSITIONED:
            return True
        else:
            return False

    async def run(self, data: TaskData) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """
        selector = await self.__comm(data).proxy(self.selector, IMode)
        await selector.set_mode(self.mode)


__all__ = ["SelectorScript"]
