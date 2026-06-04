from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any

from pyobs.object import Object
from pyobs.utils.time import Time

from .task import Project, Task


class TaskArchive(Object, metaclass=ABCMeta):
    def __init__(self, on_tasks_changed: Callable[[], Coroutine[Any, Any, None]] | None = None, **kwargs: Any):
        Object.__init__(self, **kwargs)
        self._on_tasks_changed = on_tasks_changed

    @abstractmethod
    async def last_changed(self) -> Time | None:
        """Returns time when last time any tasks changed."""
        ...

    @abstractmethod
    async def get_projects(self) -> list[Project]:
        """Returns list of projects.

        Returns:
            List of projects.
        """
        ...

    @abstractmethod
    async def get_schedulable_tasks(self) -> list[Task]:
        """Returns list of schedulable tasks.

        Returns:
            List of schedulable tasks
        """
        ...

    @abstractmethod
    async def get_task(self, id: Any) -> Task | None:
        """Returns the task with the given ID.

        Returns:
            Task with given ID.
        """
        ...


__all__ = ["TaskArchive"]
