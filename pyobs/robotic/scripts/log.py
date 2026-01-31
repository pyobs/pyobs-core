from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class LogRunner(Script):
    """Script for logging something."""

    expression: str

    async def can_run(self, data: TaskData) -> bool:
        return True

    async def run(self, data: TaskData) -> None:
        # evaluate condition
        value = eval(self.expression, {"now": datetime.now(timezone.utc), "config": self.configuration})

        # log it
        log.info(value)


__all__ = ["LogRunner"]
