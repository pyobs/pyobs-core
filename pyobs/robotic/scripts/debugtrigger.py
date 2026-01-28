from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic import TaskRunner, ObservationArchive, TaskArchive
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
        task_runner: TaskRunner | None = None,
        observation_archive: ObservationArchive | None = None,
        task_archive: TaskArchive | None = None,
    ) -> None:
        self.triggered = True


__all__ = ["DebugTriggerRunner"]
