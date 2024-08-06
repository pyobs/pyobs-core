from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Optional, List, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class LogRunner(Script):
    """Script for logging something."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        expression: str,
        **kwargs: Any,
    ):
        """Initialize a new LogRunner.

        Args:
            expression: expression to check
        """
        Script.__init__(self, **kwargs)
        self.expression = expression

    async def can_run(self) -> bool:
        return True

    async def run(
        self,
        task_runner: TaskRunner,
        task_schedule: Optional[TaskSchedule] = None,
        task_archive: Optional[TaskArchive] = None,
    ) -> None:
        # evaluate condition
        value = eval(self.expression, {"now": datetime.now(timezone.utc), "config": self.configuration})

        # log it
        log.info(value)


__all__ = ["LogRunner"]
