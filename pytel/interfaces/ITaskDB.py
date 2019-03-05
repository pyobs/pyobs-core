from pytel.utils.time import Time

from .interface import *


class ITaskDB(Interface):
    def list_tasks(self, *args, **kwargs) -> list:
        """Lists all tasks in database.

        Returns:
            (list) List of task IDs.
        """
        raise NotImplementedError

    def calculate_merits(self, time: Time, *args, **kwargs) -> dict:
        """Calculates and returns tasks for all tasks.

        Args:
            time (Time): Time at which to calculate tasks.

        Returns:
            (dict) Dictionary with Task/Merit pairs.
        """
        raise NotImplementedError

    def run_task(self, task_id: str, *args, **kwargs):
        """Run a task.

        Args:
            task_id (str): Unique ID of task to run.
        """

    def abort_task(self, *args, **kwargs):
        """Abort current task."""
        raise NotImplementedError


__all__ = ['ITaskDB']
