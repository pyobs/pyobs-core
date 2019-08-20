from pyobs.utils.time import Time
from .task import Task


class Scheduler:
    def get_task(self, time: Time) -> Task:
        """Returns the active task at the given time.

        Args:
            time: Time to return task for.

        Returns:
            Task at the given time.
        """
        raise NotImplementedError


__all__ = ['Scheduler']
