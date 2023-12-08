from __future__ import annotations
import asyncio
import logging
from typing import Any, Dict, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive
from pyobs.robotic.scripts import Script


log = logging.getLogger(__name__)


class ParallelRunner(Script):
    """Script for running other scripts in parallel."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        scripts: List[Dict[str, Any]],
        **kwargs: Any,
    ):
        """Initialize a new ParallelRunner.

        Args:
            scripts: list or dict of scripts to run in parallel.
        """
        Script.__init__(self, **kwargs)
        self.scripts = scripts

    async def can_run(self) -> bool:
        return True

    async def run(
        self,
        task_runner: TaskRunner,
        task_schedule: Optional[TaskSchedule] = None,
        task_archive: Optional[TaskArchive] = None,
    ) -> None:
        tasks = [
            asyncio.create_task(self.get_object(s, Script).run(task_runner, task_schedule, task_archive))
            for s in self.scripts
        ]
        await asyncio.gather(*tasks)


__all__ = ["ParallelRunner"]
