from __future__ import annotations
from typing import Any, TYPE_CHECKING, Optional, Dict

from pyobs.object import Object
from .task import Task

if TYPE_CHECKING:
    from .observationarchive import ObservationArchive
    from .taskarchive import TaskArchive


class TaskRunner(Object):
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

    async def run_task(
        self,
        task: Task,
        observation_archive: ObservationArchive | None = None,
        task_archive: TaskArchive | None = None,
    ) -> bool:
        """Run a task.

        Args:
            task: Task to run
            observation_archive: Schedule.
            task_archive: Archive.

        Returns:
            Success or not
        """

        # run task
        await task.run(
            task_runner=self, observation_archive=observation_archive, task_archive=task_archive, scripts=self.scripts
        )

        # finish
        return True


__all__ = ["TaskRunner"]
