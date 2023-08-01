import logging
from pyobs.modules.robotic import ScriptRunner
from typing import Any, Dict, Optional, Union, List

from pyobs.object import get_object
from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class SequentialRunner(Script):
    """Script for running a sequence of other scripts."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        scripts: List[Dict[str, Any]],
        **kwargs: Any,
    ):
        """Initialize a new SequentialRunner.

        Args:
            script: list or dict of scripts to run in a sequence.
        """
        if "configuration" not in kwargs:
            kwargs["configuration"] = {}
        Script.__init__(self, **kwargs)

        for script in scripts:
            script["comm"] = self.comm
        self.scripts = scripts

    async def can_run(self) -> bool:
        return True

    async def run(
        self,
        task_runner: TaskRunner,
        task_schedule: Optional[TaskSchedule] = None,
        task_archive: Optional[TaskArchive] = None,
    ) -> None:
        for s in self.scripts:
            await get_object(s, Script).run(task_runner, task_schedule, task_archive)


__all__ = ["SequentialRunner"]
