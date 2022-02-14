from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Any, TYPE_CHECKING, Optional, Dict

from pyobs.object import Object
from .task import Task

if TYPE_CHECKING:
    from .taskschedule import TaskSchedule
    from .taskarchive import TaskArchive


class TaskRunner(Object, metaclass=ABCMeta):
    def __init__(
        self,
        scripts: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """Creates a new LCO scheduler.

        Args:
            scripts: External scripts
        """
        Object.__init__(self, **kwargs)

        # store stuff
        self.scripts = scripts

    async def can_run(self, task: Task) -> bool:
        """Checks, whether this task could run now.

        Returns:
            True, if task can run now.
        """
        return await task.can_run(self.scripts)

    @abstractmethod
    async def run_task(
        self, task: Task, task_schedule: Optional[TaskSchedule] = None, task_archive: Optional[TaskArchive] = None
    ) -> bool:
        """Run a task.

        Args:
            task: Task to run
            task_schedule: Schedule.
            task_archive: Archive.

        Returns:
            Success or not
        """

        # run task
        await task.run(task_runner=self, task_schedule=task_schedule, task_archive=task_archive, scripts=self.scripts)

        # finish
        return True


__all__ = ["TaskRunner"]
