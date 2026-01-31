from __future__ import annotations
from typing import Any

from pyobs.object import Object
from . import ObservationArchive, TaskArchive
from .task import Task, TaskData


class TaskRunner(Object):

    def __init__(
        self,
        observation_archive: ObservationArchive | None = None,
        task_archive: TaskArchive | None = None,
        **kwargs: Any,
    ):
        """Creates a new LCO scheduler.

        Args:
            scripts: External scripts
        """
        Object.__init__(self, **kwargs)

        # store stuff
        self.observation_archive = observation_archive
        self.task_archive = task_archive

    def __task_data(self, task: Task) -> TaskData:
        return TaskData(
            task=task,
            observation_archive=self.observation_archive,
            task_archive=self.task_archive,
            observer=self.observer,
            comm=self.comm,
        )

    async def can_run(self, task: Task) -> bool:
        """Checks, whether this task could run now.

        Args:
            task: Task to run

        Returns:
            True, if task can run now.
        """
        return await task.can_run(self.__task_data(task))

    async def run_task(self, task: Task) -> bool:
        """Run a task.

        Args:
            task: Task to run

        Returns:
            Success or not
        """

        # run task
        await task.run(self.__task_data(task))

        # finish
        return True


__all__ = ["TaskRunner"]
