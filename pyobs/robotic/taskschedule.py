from abc import ABCMeta, abstractmethod
from typing import Any, Type
from astroplan import ObservingBlock

from pyobs.utils.time import Time
from .task import Task, ScheduledTask
from pyobs.object import Object


class TaskSchedule(Object, metaclass=ABCMeta):
    def __init__(self, **kwargs: Any):
        Object.__init__(self, **kwargs)

    @abstractmethod
    async def set_schedule(self, blocks: list[ObservingBlock], start_time: Time) -> None:
        """Set the list of scheduled blocks.

        Args:
            blocks: Scheduled blocks.
            start_time: Start time for schedule.
        """
        ...

    @abstractmethod
    async def last_scheduled(self) -> Time | None:
        """Returns time of last scheduler run."""
        ...

    @abstractmethod
    async def get_schedule(self) -> list[ScheduledTask]:
        """Fetch schedule from portal.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            ValueError: If something goes wrong.
        """
        ...

    @abstractmethod
    async def get_task(self, time: Time) -> Task | None:
        """Returns the active task at the given time.

        Args:
            time: Time to return task for.

        Returns:
            Task at the given time.
        """
        ...

    def _create_task(self, klass: Type[Task], **kwargs: Any) -> Task:
        return self.get_object(klass, Task, tasks=self, **kwargs)


__all__ = ["TaskSchedule"]
