from abc import ABCMeta, abstractmethod
from typing import Any

from pyobs.object import Object
from .task import Task
from .observation import Observation


class ObservationArchive(Object, metaclass=ABCMeta):
    def __init__(self, **kwargs: Any):
        Object.__init__(self, **kwargs)

    @abstractmethod
    async def observations(self, task: Task) -> list[Observation]:
        """Returns list of observations for the given task.

        Args:
            task: Task to get observations for.

        Returns:
            List of observations for the given task.
        """
        ...


__all__ = ["ObservationArchive"]
