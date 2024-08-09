from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional, List, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class CasesRunner(Script):
    """Script for distinguishing cases."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        expression: str,
        cases: Dict[Union[str, int, float], Any],
        **kwargs: Any,
    ):
        """Initialize a new CasesRunner.

        Args:
            expression: expression to check
            cases: dictionary with cases
        """
        Script.__init__(self, **kwargs)
        self.expression = expression
        self.cases = cases

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

        # check in cases
        if value in self.cases:
            await self.get_object(self.cases[value], Script).run(task_runner, task_schedule, task_archive)
        elif "else" in self.cases:
            await self.get_object(self.cases["else"], Script).run(task_runner, task_schedule, task_archive)


__all__ = ["CasesRunner"]
