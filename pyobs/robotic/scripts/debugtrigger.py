from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Optional, List, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class DebugTriggerRunner(Script):
    """Script for a debug trigger."""

    __module__ = "pyobs.modules.robotic"

    def __init__(self, **kwargs: Any):
        """Initialize a new DebugTriggerRunner."""
        Script.__init__(self, **kwargs)
        self.triggered = False

    async def can_run(self) -> bool:
        return True

    async def run(
        self,
        task_runner: TaskRunner,
        task_schedule: Optional[TaskSchedule] = None,
        task_archive: Optional[TaskArchive] = None,
    ) -> None:
        self.triggered = True


__all__ = ["DebugTriggerRunner"]
