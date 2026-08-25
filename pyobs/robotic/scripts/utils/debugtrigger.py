from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class DebugTriggerScript(Script):
    """Script for a debug trigger."""

    triggered: bool = Field(default=False, description="Set to True once this script has run.")

    async def can_run(self, data: TaskData | None) -> bool:
        return True

    async def run(self, data: TaskData | None) -> None:
        self.triggered = True


__all__ = ["DebugTriggerScript"]
