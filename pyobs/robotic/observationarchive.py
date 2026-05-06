from __future__ import annotations
import datetime
from abc import ABCMeta, abstractmethod
from typing import Any, TYPE_CHECKING

from pyobs.utils.time import Time
from pyobs.object import Object

if TYPE_CHECKING:
    from . import Task, TaskArchive
    from .observation import ObservationList, Observation, ObservationState


class ObservationArchive(Object, metaclass=ABCMeta):
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
    async def get_task(self, time: Time, task_archive: TaskArchive | None = None) -> Observation | None:
        """Returns the active scheduled task at the given time.

        Args:
            time: Time to return task for.
            task_archive: Task archive to get task from.

        Returns:
            Scheduled task at the given time.
        """
        ...

    @abstractmethod
    async def get_current_observation(self, task_archive: TaskArchive | None = None) -> Observation | None:
        """Returns the currently running observation.

        Args:
            task_archive: Task archive to get task from.

        Returns:
            Currently running observation.
        """
        ...

    @abstractmethod
    async def update_observation_state(self, observation: Observation, state: ObservationState) -> None:
        """Updates observation state to given status.
        Args:
            observation: Observation to update.
            state: Observation state.
        """
        ...

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
