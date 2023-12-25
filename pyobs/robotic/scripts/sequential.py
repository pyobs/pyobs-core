from __future__ import annotations
import logging
from typing import Any, Dict, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class SequentialRunner(Script):
    """Script for running a sequence of other scripts."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        scripts: List[Dict[str, Any]],
        check_all_can_run: bool = True,
        **kwargs: Any,
    ):
        """Initialize a new SequentialRunner.

        Args:
            script: list or dict of scripts to run in a sequence.
        """
        Script.__init__(self, **kwargs)
        self.scripts = scripts
        self.check_all_can_run = check_all_can_run

    async def can_run(self) -> bool:
        check_all = [await self.get_object(s, Script).can_run() for s in self.scripts]
        return all(check_all) if self.check_all_can_run else check_all[0]

    async def run(
        self,
        task_runner: TaskRunner,
        task_schedule: Optional[TaskSchedule] = None,
        task_archive: Optional[TaskArchive] = None,
    ) -> None:
        for s in self.scripts:
            script = self.get_object(s, Script)
            if script.can_run():
                await script.run(task_runner, task_schedule, task_archive)


__all__ = ["SequentialRunner"]
