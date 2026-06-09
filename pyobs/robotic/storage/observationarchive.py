from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any

from pyobs.object import Object
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic import Task, TaskArchive
    from pyobs.robotic.observation import Observation, ObservationList, ObservationState


class ObservationArchive(Object, metaclass=ABCMeta):
    def __init__(self, **kwargs: Any):
        Object.__init__(self, **kwargs)

    @abstractmethod
    async def add_observations(self, tasks: ObservationList) -> None:
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
    async def get_schedule(self, time: Time | None = None) -> ObservationList:
        """Fetch schedule.

        Args:
            time: Time to fetch schedule for. Defaults to now.

        Returns:
            Dictionary with tasks.

        Raises:
            Timeout: If request timed out.
            ValueError: If something goes wrong.
        """
        ...

    @abstractmethod
    async def get_next_observation(self, time: Time, task_archive: TaskArchive | None = None) -> Observation | None:
        """Returns the active scheduled task at the given time.

        Args:
            time: Time to return task for.
            task_archive: Task archive to get task from.

        Returns:
            Scheduled task at the given time.
        """
        ...

    @abstractmethod
    async def get_current_observation(
        self, task_archive: TaskArchive | None = None, time: Time | None = None
    ) -> Observation | None:
        """Returns the currently running observation.

        Args:
            task_archive: Task archive to get task from.
            time: Time to check for. Defaults to now.

        Returns:
            Currently running observation.
        """
        ...

    @abstractmethod
    async def update_observation(self, observation: Observation) -> None:
        """Updates observation.
        Args:
            observation: Observation to update.
        """
        ...

    @abstractmethod
    async def get_observations(
        self,
        task: Task | None = None,
        state: ObservationState | None = None,
        start_before: Time | None = None,
        start_after: Time | None = None,
        end_before: Time | None = None,
        end_after: Time | None = None,
    ) -> ObservationList:
        """Returns a list of observations matching the given filters.

        Args:
            task: If given, only return observations for this task.
            state: If given, only return observations in this state.
            start_before: If given, only return observations that start before this time.
            start_after: If given, only return observations that start after this time.
            end_before: If given, only return observations that end before this time.
            end_after: If given, only return observations that end after this time.

        Returns:
            List of matching observations.
        """
        ...


__all__ = ["ObservationArchive"]
