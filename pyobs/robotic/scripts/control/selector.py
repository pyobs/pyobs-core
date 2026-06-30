from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyobs.interfaces import IMotion
from pyobs.interfaces.IMode import IMode
from pyobs.robotic.scripts import Script
from pyobs.utils.enums import MotionStatus

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
    from pyobs.utils.time import Time

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
        if not await self.comm.has_proxy(self.selector, IMode):
            self._cant_run_reason = "No selector found."
            return False
        async with self.comm.proxy(self.selector, IMotion) as selector:
            motion_state = await selector.wait_for_state(IMotion, timeout=5.0)
            status = motion_state.status if motion_state is not None else MotionStatus.UNKNOWN
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
        async with self.comm.proxy(self.selector, IMode) as selector:
            await selector.set_mode(self.mode)

    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        """Estimate duration of the mode change."""
        # TODO: get a better estimate for mode-change durations
        return 30.0


__all__ = ["SelectorScript"]
