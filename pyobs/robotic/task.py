from abc import ABCMeta, abstractmethod
from typing import Tuple, TYPE_CHECKING, Any, Optional, List, Dict

from pyobs.object import Object
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic.taskschedule import TaskSchedule


class Task(Object, metaclass=ABCMeta):
    def __init__(self, schedule: "TaskSchedule", **kwargs: Any):
        Object.__init__(self, **kwargs)
        self.schedule = schedule

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
    async def can_run(self) -> bool:
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
    async def run(self) -> None:
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
