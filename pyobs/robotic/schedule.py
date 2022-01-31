from abc import ABCMeta, abstractmethod
from typing import Optional, Any, List, Dict, Type
from astroplan import ObservingBlock

from pyobs.utils.time import Time
from .task import Task
from pyobs.object import Object


class Schedule(Object, metaclass=ABCMeta):
    def __init__(self, **kwargs: Any):
        Object.__init__(self, **kwargs)

    async def open(self) -> None:
        pass

    async def close(self) -> None:
        pass

    @abstractmethod
    async def last_scheduled(self) -> Optional[Time]:
        """Returns time of last scheduler run."""
        ...

    @abstractmethod
    async def update_schedule(self, blocks: List[ObservingBlock], start_time: Time) -> None:
        """Update the list of scheduled blocks.

        Args:
            blocks: Scheduled blocks.
            start_time: Start time for schedule.
        """
        ...

    def _create_task(self, klass: Type[Task], **kwargs: Any) -> Task:
        return self.get_object(klass, tasks=self, **kwargs)

    @abstractmethod
    def get_task(self, time: Time) -> Optional[Task]:
        """Returns the active task at the given time.

        Args:
            time: Time to return task for.

        Returns:
            Task at the given time.
        """
        ...

    @abstractmethod
    async def run_task(self, task: Task) -> bool:
        """Run a task.

        Args:
            task: Task to run

        Returns:
            Success or not
        """
        ...

    @abstractmethod
    async def get_schedule(self, start_before: Time, end_after: Time, include_running: bool = True) -> Dict[str, Task]:
        """Fetch schedule from portal.

        Args:
            start_before: Task must start before this time.
            end_after: Task must end after this time.
            include_running: Whether to include a currently running task.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            ValueError: If something goes wrong.
        """
        ...


__all__ = ["Schedule"]
