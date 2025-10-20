from dataclasses import dataclass
from astropy.time import Time

from pyobs.robotic import Task


@dataclass
class TaskSuccess:
    date: Time
    night: Time


class DataProvider:
    """Data provider for Merit classes."""

    def __init__(self) -> None:
        self._task_success: dict[Task, list[TaskSuccess]] = {}

    def reset(self) -> None:
        """Reset data provider."""
        self._task_success.clear()

    def get_night(self) -> Time:
        """Returns the current night."""
        return Time.now()

    def get_task_success_count(self, task: Task) -> int:
        """Return the number of successful runs for task."""
        if task not in self._task_success:
            return 0
        return len(self._task_success[task])

    def get_task_success(self, task: Task, number: int = -1) -> TaskSuccess | None:
        """Return the number of successful runs for task."""
        try:
            return self._task_success[task][number]
        except IndexError:
            return None


__all__ = ["DataProvider"]
