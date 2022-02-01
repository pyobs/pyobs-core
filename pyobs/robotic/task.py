from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Tuple, TYPE_CHECKING, Any, Optional, List, Dict

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

    @property
    @abstractmethod
    def start(self) -> Time:
        """Start time for task"""
        ...

    @property
    @abstractmethod
    def end(self) -> Time:
        """End time for task"""
        ...

    @abstractmethod
    async def can_run(self, scripts: Optional[Dict[str, Script]] = None) -> bool:
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
        task_schedule: Optional[TaskSchedule] = None,
        task_archive: Optional[TaskArchive] = None,
        scripts: Optional[Dict[str, Script]] = None,
    ) -> None:
        """Run a task"""
        ...

    @abstractmethod
    def is_finished(self) -> bool:
        """Whether task is finished."""
        ...

    def get_fits_headers(self, namespaces: Optional[List[str]] = None) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        return {}


__all__ = ["Task"]
