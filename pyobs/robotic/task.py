from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any
from astropy.units import Quantity
import astropy.units as u

from pyobs.object import Object
from pyobs.robotic.scheduler.targets import Target
from pyobs.robotic.scripts import Script
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic.taskschedule import TaskSchedule
    from pyobs.robotic.taskrunner import TaskRunner
    from pyobs.robotic.taskarchive import TaskArchive
    from pyobs.robotic.scheduler.constraints import Constraint
    from pyobs.robotic.scheduler.merits import Merit


class Task(Object, metaclass=ABCMeta):

    def __init__(
        self,
        id: Any,
        name: str,
        duration: float,
        priority: float | None = None,
        config: dict[str, Any] | None = None,
        constraints: list[Constraint] | None = None,
        merits: list[Merit] | None = None,
        target: Target | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._id = id
        self._name = name
        self._duration = duration
        self._priority = priority
        self._config = config
        self._constraints = constraints
        self._merits = merits
        self._target = target

    @property
    def id(self) -> Any:
        """ID of task."""
        return self._id

    @property
    def name(self) -> str:
        """Returns name of task."""
        return self._name

    @property
    def duration(self) -> Quantity:
        """Returns estimated duration of task in seconds."""
        return self._duration * u.second

    @property
    def priority(self) -> float:
        """Returns priority."""
        return self._priority if self._priority is not None else 0.0

    @property
    def config(self) -> dict[str, Any]:
        """Returns configuration."""
        return self._config if self._config is not None else {}

    @property
    def constraints(self) -> list[Constraint]:
        """Returns constraints."""
        return self._constraints if self._constraints is not None else []

    @property
    def merits(self) -> list[Merit]:
        """Returns merits."""
        return self._merits if self._merits is not None else []

    @property
    def target(self) -> Target | None:
        """Returns target."""
        return self._target

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
            return any(self.start < other.start)
        raise NotImplementedError

    def __gt__(self, other: object) -> bool:
        if isinstance(other, ScheduledTask):
            return any(self.start > other.start)
        raise NotImplementedError

    def __le__(self, other: object) -> bool:
        if isinstance(other, ScheduledTask):
            return any(self.start <= other.start)
        raise NotImplementedError

    def __ge__(self, other: object) -> bool:
        if isinstance(other, ScheduledTask):
            return any(self.start >= other.start)
        raise NotImplementedError


__all__ = ["Task", "ScheduledTask"]
