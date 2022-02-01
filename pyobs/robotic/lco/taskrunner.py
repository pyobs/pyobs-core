import logging
from typing import Dict, Optional, Any

from pyobs.robotic.task import Task
from pyobs.robotic.taskrunner import TaskRunner
from pyobs.robotic import TaskSchedule, TaskArchive
from pyobs.robotic.lco import LcoTaskSchedule

log = logging.getLogger(__name__)


class LcoTaskRunner(TaskRunner):
    """Scheduler for using the LCO portal"""

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

        # force update tasks
        if isinstance(task_schedule, LcoTaskSchedule):
            await task_schedule.update_now(force=True)

        # finish
        return True


__all__ = ["LcoTaskRunner"]
