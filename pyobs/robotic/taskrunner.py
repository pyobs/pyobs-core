from abc import ABCMeta, abstractmethod
from typing import Any

from pyobs.object import Object
from .task import Task


class TaskRunner(Object, metaclass=ABCMeta):
    def __init__(self, **kwargs: Any):
        Object.__init__(self, **kwargs)

    async def open(self) -> None:
        pass

    async def close(self) -> None:
        pass

    @abstractmethod
    async def run_task(self, task: Task) -> bool:
        """Run a task.

        Args:
            task: Task to run

        Returns:
            Success or not
        """
        ...


__all__ = ["TaskRunner"]
