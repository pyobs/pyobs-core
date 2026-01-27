from abc import ABCMeta, abstractmethod
from typing import Any, Type, cast

from pyobs.utils.time import Time
from .task import Task
from .observation import ObservationList, Observation
from pyobs.object import Object


class TaskSchedule(Object, metaclass=ABCMeta):
    def __init__(self, **kwargs: Any):
        Object.__init__(self, **kwargs)

    @abstractmethod
    async def add_schedule(self, tasks: ObservationList) -> None:
        """Add the list of scheduled tasks to the schedule.

        Args:
            tasks: Scheduled tasks.
        """
        ...

    @abstractmethod
    async def clear_schedule(self, start_time: Time) -> None:
        """Clear schedule after given start time.

        Args:
            start_time: Start time to clear from.
        """
        ...

    @abstractmethod
    async def last_scheduled(self) -> Time | None:
        """Returns time of last scheduler run."""
        ...

    @abstractmethod
    async def get_schedule(self) -> ObservationList:
        """Fetch schedule from portal.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            ValueError: If something goes wrong.
        """
        ...

    @abstractmethod
    async def get_task(self, time: Time) -> Observation | None:
        """Returns the active scheduled task at the given time.

        Args:
            time: Time to return task for.

        Returns:
            Scheduled task at the given time.
        """
        ...

    def _create_task(self, klass: Type[Task], **kwargs: Any) -> Task:
        return cast(Task, self.get_object(klass, Task, tasks=self, **kwargs))


__all__ = ["TaskSchedule"]
