from abc import ABCMeta, abstractmethod
from typing import Any

from pyobs.utils.time import Time
from pyobs.object import Object
from .task import Task


class TaskArchive(Object, metaclass=ABCMeta):
    def __init__(self, **kwargs: Any):
        Object.__init__(self, **kwargs)

    @abstractmethod
    async def last_changed(self) -> Time | None:
        """Returns time when last time any tasks changed."""
        ...

    @abstractmethod
    async def get_schedulable_tasks(self) -> list[Task]:
        """Returns list of schedulable tasks.

        Returns:
            List of schedulable tasks
        """
        ...


__all__ = ["TaskArchive"]
