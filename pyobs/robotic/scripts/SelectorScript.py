from __future__ import annotations
import logging
from typing import Any, Optional, TYPE_CHECKING

from pyobs.interfaces.IMode import IMode
from pyobs.robotic.scripts import Script
from pyobs.utils.enums import MotionStatus

if TYPE_CHECKING:
    from pyobs.robotic import TaskSchedule, TaskArchive, TaskRunner

log = logging.getLogger(__name__)


class SelectorScript(Script):
    """Script for running Mode Selection."""

    def __init__(
        self,
        mode: str,
        selector: str,
        **kwargs: Any,
    ):
        """Init a new select_mode script.
        Args:
            mode: mode that will be selected
            selector: name of the mode selector module, e.g. LinearModeSelector
        """
        Script.__init__(self, **kwargs)
        # store modules
        self.mode = mode
        self.selector_name = selector

    #        self.selector = await self.proxy(selector)

    async def can_run(self) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """
        # check if selector is ready
        selector = await self.comm.proxy(self.selector_name)
        status = selector.get_motion_status()
        if status == MotionStatus.PARKED or status == MotionStatus.POSITIONED:
            return True
        else:
            return False

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
        selector = await self.comm.proxy(self.selector_name)
        selector.set_mode(self.mode)


__all__ = ["SelectorScript"]
