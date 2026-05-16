from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class DebugTriggerRunner(Script):
    """Script for a debug trigger."""

    triggered: bool = False

    async def can_run(self, data: TaskData) -> bool:
        return True

    async def run(self, data: TaskData) -> None:
        self.triggered = True


__all__ = ["DebugTriggerRunner"]
