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

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """
        # check if selector is ready
        selector = await self.comm.proxy(self.selector, IMode)
        status = await selector.get_motion_status()
        if status == MotionStatus.PARKED or status == MotionStatus.POSITIONED:
            self._cant_run_reason = None
            return True
        else:
            self._cant_run_reason = f"Selector not ready: {status.name}"
            return False

    async def run(self, data: TaskData | None) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """
        selector = await self.comm.proxy(self.selector, IMode)
        await selector.set_mode(self.mode)


__all__ = ["SelectorScript"]
