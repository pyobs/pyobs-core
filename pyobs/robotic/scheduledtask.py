from __future__ import annotations
from typing import TYPE_CHECKING
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic.task import Task


class ScheduledTask:
    """A scheduled task."""

    def __init__(self, task: Task, start: Time, end: Time):
        self._task = task
        self._start = start
        self._end = end

    @property
    def task(self) -> Task:
        """Returns the task."""
        return self._task

    @property
    def start(self) -> Time:
        """Start time for task"""
        return self._start

    @property
    def end(self) -> Time:
        """End time for task"""
        return self._end

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ScheduledTask):
            return self.task.id == other.task.id and self.start == other.start and self.end == other.end
        return super().__eq__(other)

    def __ne__(self, other: object) -> bool:
        if isinstance(other, ScheduledTask):
            return self.task.id != other.task.id or self.start != other.start or self.end != other.end
        return super().__ne__(other)

    def __lt__(self, other: object) -> bool:
        if isinstance(other, ScheduledTask):
            return bool(self.start < other.start)
        raise NotImplementedError

    def __gt__(self, other: object) -> bool:
        if isinstance(other, ScheduledTask):
            return bool(self.start > other.start)
        raise NotImplementedError

    def __le__(self, other: object) -> bool:
        if isinstance(other, ScheduledTask):
            return bool(self.start <= other.start)
        raise NotImplementedError

    def __ge__(self, other: object) -> bool:
        if isinstance(other, ScheduledTask):
            return bool(self.start >= other.start)
        raise NotImplementedError


__all__ = ["ScheduledTask"]
