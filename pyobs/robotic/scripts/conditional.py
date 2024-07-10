from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class ConditionalRunner(Script):
    """Script for running an if condition."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        condition: str,
        true: Dict[str, Any],
        false: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """Initialize a new ConditionalRunner.

        Args:
            condition: condition to check
            true: script to run if condition is evaluated as True
            false: script to run otherwise.
        """
        Script.__init__(self, **kwargs)
        self.condition = condition
        self.true = true
        self.false = false

    async def can_run(self) -> bool:
        return True

    async def run(
        self,
        task_runner: TaskRunner,
        task_schedule: Optional[TaskSchedule] = None,
        task_archive: Optional[TaskArchive] = None,
    ) -> None:
        # evaluate condition
        ret = eval(self.condition, {"now": datetime.now(timezone.utc)})

        # run scripts
        if ret:
            await self.get_object(self.true, Script).run(task_runner, task_schedule, task_archive)
        else:
            if self.false is not None:
                await self.get_object(self.false, Script).run(task_runner, task_schedule, task_archive)


__all__ = ["ConditionalRunner"]
