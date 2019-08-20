from pyobs.robotic.task import Task
from pyobs.utils.time import Time
from ..scheduler import Scheduler
from .task import LcoTask


class LcoScheduler(Scheduler):
    def __init__(self, *args, **kwargs):
        self._task = LcoTask()

    def get_task(self, time: Time) -> Task:
        """Returns the active task at the given time.

        Args:
            time: Time to return task for.

        Returns:
            Task at the given time.
        """

        if self._task.is_finished():
            return None
        else:
            return self._task


__all__ = ['LcoScheduler']
