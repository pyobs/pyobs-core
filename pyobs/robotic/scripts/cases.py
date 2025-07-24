from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, TYPE_CHECKING

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
        cases: dict[str | int | float, Any],
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

    def __get_script(self) -> Script:
        # evaluate condition
        value = eval(self.expression, {"now": datetime.now(timezone.utc), "config": self.configuration})

        # check in cases
        if value in self.cases:
            return self.get_object(self.cases[value], Script, configuration=self.configuration)
        elif "else" in self.cases:
            return self.get_object(self.cases["else"], Script, configuration=self.configuration)
        else:
            raise ValueError("Invalid choice")

    async def can_run(self) -> bool:
        script = self.__get_script()
        return await script.can_run()

    async def run(
        self,
        task_runner: TaskRunner | None = None,
        task_schedule: TaskSchedule | None = None,
        task_archive: TaskArchive | None = None,
    ) -> None:
        script = self.__get_script()
        await script.run(task_runner, task_schedule, task_archive)


__all__ = ["CasesRunner"]
