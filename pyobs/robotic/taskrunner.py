from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Any, TYPE_CHECKING, Optional

from pyobs.object import Object
from .task import Task

if TYPE_CHECKING:
    from .taskschedule import TaskSchedule
    from .taskarchive import TaskArchive


class TaskRunner(Object, metaclass=ABCMeta):
    def __init__(self, **kwargs: Any):
        Object.__init__(self, **kwargs)

    async def open(self) -> None:
        pass

    async def close(self) -> None:
        pass

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
        ...


__all__ = ["TaskRunner"]
