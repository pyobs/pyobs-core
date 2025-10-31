from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any

from pyobs.object import Object
from pyobs.robotic.scripts import Script
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic.taskschedule import TaskSchedule
    from pyobs.robotic.taskrunner import TaskRunner
    from pyobs.robotic.taskarchive import TaskArchive


class Task(Object, metaclass=ABCMeta):
    @property
    @abstractmethod
    def id(self) -> Any:
        """ID of task."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns name of task."""
        ...

    @property
    @abstractmethod
    def duration(self) -> float:
        """Returns estimated duration of task in seconds."""
        ...

    @abstractmethod
    async def can_run(self, scripts: dict[str, Script] | None = None) -> bool:
        """Checks, whether this task could run now.

        Returns:
            True, if task can run now.
        """
        ...

    @property
    @abstractmethod
    def can_start_late(self) -> bool:
        """Whether this tasks is allowed to start later than the user-set time, e.g. for flatfields.

        Returns:
            True, if task can start late.
        """
        ...

    @abstractmethod
    async def run(
        self,
        task_runner: TaskRunner,
        task_schedule: TaskSchedule | None = None,
        task_archive: TaskArchive | None = None,
        scripts: dict[str, Script] | None = None,
    ) -> None:
        """Run a task"""
        ...

    @abstractmethod
    def is_finished(self) -> bool:
        """Whether task is finished."""
        ...

    def get_fits_headers(self, namespaces: list[str] | None = None) -> dict[str, tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        return {}


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


__all__ = ["Task", "ScheduledTask"]
