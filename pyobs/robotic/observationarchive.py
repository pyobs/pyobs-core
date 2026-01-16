from __future__ import annotations
from abc import ABCMeta, abstractmethod
import datetime
from typing import Any, TYPE_CHECKING

from pyobs.object import Object

if TYPE_CHECKING:
    from .task import Task
    from .observation import ObservationList


class ObservationArchive(Object, metaclass=ABCMeta):
    def __init__(self, **kwargs: Any):
        Object.__init__(self, **kwargs)

    @abstractmethod
    async def observations_for_task(self, task: Task) -> ObservationList:
        """Returns list of observations for the given task.

        Args:
            task: Task to get observations for.

        Returns:
            List of observations for the given task.
        """
        ...

    @abstractmethod
    async def observations_for_night(self, date: datetime.date) -> ObservationList:
        """Returns list of observations for the given task.

        Args:
            date: Date of night to get observations for.

        Returns:
            List of observations for the given task.
        """
        ...


__all__ = ["ObservationArchive"]
