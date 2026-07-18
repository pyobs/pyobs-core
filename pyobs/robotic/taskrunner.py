from __future__ import annotations

from typing import Any

from pyobs.object import Object

from . import ObservationArchive, TaskArchive
from .scheduler.targets import Target
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

    def __task_data(self, task: Task, target: Target | None = None) -> TaskData:
        return TaskData(
            task=task,
            observation_archive=self.observation_archive,
            task_archive=self.task_archive,
            target=target,
        )

    async def can_run(self, task: Task, target: Target | None = None) -> bool:
        """Checks, whether this task could run now.

        Args:
            task: Task to run
            target: Resolved target for this specific run, e.g. from the scheduled observation.

        Returns:
            True, if task can run now.
        """
        return await task.can_run(self.__task_data(task, target))

    def cant_run_reason(self, task: Task) -> str | None:
        """Returns reason why task cannot run, or None if it can."""
        return task.cant_run_reason()

    async def run_task(self, task: Task, target: Target | None = None) -> bool:
        """Run a task.

        Args:
            task: Task to run
            target: Resolved target for this specific run, e.g. from the scheduled observation.

        Returns:
            Success or not
        """

        # run task
        await task.run(self.__task_data(task, target))

        # finish
        return True


__all__ = ["TaskRunner"]
