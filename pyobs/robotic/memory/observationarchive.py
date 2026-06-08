from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyobs.robotic.observation import Observation, ObservationList, ObservationState
from pyobs.robotic.observationarchive import ObservationArchive
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic.task import Task
    from pyobs.robotic.taskarchive import TaskArchive


class MemoryObservationArchive(ObservationArchive):
    """In-memory observation archive for testing and simple deployments."""

    def __init__(self, **kwargs: Any):
        ObservationArchive.__init__(self, **kwargs)
        self._observations: ObservationList = ObservationList()

    async def add_observations(self, observations: ObservationList) -> None:
        """Add observations to the archive.

        Args:
            observations: Observations to add.
        """
        self._observations.extend(observations)

    async def clear_schedule(self, start_time: Time) -> None:
        """Remove all PENDING observations that end after start_time.

        Args:
            start_time: Remove pending observations ending after this time.
        """
        self._observations = ObservationList(
            [obs for obs in self._observations if not (obs.state == ObservationState.PENDING and obs.end > start_time)]
        )

    async def get_schedule(self, time: Time | None = None) -> ObservationList:
        """Return all observations.

        Args:
            time: Unused — in-memory archive holds all observations regardless of time.

        Returns:
            All stored observations.
        """
        return ObservationList(list(self._observations))

    async def get_next_observation(self, time: Time, task_archive: TaskArchive | None = None) -> Observation | None:
        """Returns the pending observation active at the given time.

        Args:
            time: Time to check.
            task_archive: Task archive to restore resolved target from.

        Returns:
            Active pending observation, or None.
        """
        for obs in self._observations:
            if obs.state == ObservationState.PENDING and obs.start <= time < obs.end:
                if task_archive is not None:
                    await obs.fetch_task(task_archive)
                return obs
        return None

    async def get_current_observation(
        self, task_archive: TaskArchive | None = None, time: Time | None = None
    ) -> Observation | None:
        """Returns the currently IN_PROGRESS observation.

        Args:
            task_archive: Task archive to restore resolved target from.
            time: Unused.

        Returns:
            IN_PROGRESS observation, or None.
        """
        for obs in self._observations:
            if obs.state == ObservationState.IN_PROGRESS:
                if task_archive is not None:
                    await obs.fetch_task(task_archive)
                return obs
        return None

    async def update_observation(self, observation: Observation) -> None:
        """Update an existing observation by UUID, or append if not found.

        Args:
            observation: Observation to update.
        """
        for i, obs in enumerate(self._observations):
            if obs.id == observation.id:
                self._observations[i] = observation
                return
        self._observations.append(observation)

    async def get_observations(
        self,
        task: Task | None = None,
        state: ObservationState | None = None,
        start_before: Time | None = None,
        start_after: Time | None = None,
        end_before: Time | None = None,
        end_after: Time | None = None,
    ) -> ObservationList:
        """Returns filtered observations.

        Args:
            task: If given, only return observations for this task.
            state: If given, only return observations in this state.
            start_before: If given, only return observations starting before this time.
            start_after: If given, only return observations starting after this time.
            end_before: If given, only return observations ending before this time.
            end_after: If given, only return observations ending after this time.

        Returns:
            Filtered list of observations.
        """
        return self._observations.filter(
            state=state,
            task_id=task.id if task is not None else None,
            start_before=start_before,
            start_after=start_after,
            end_before=end_before,
            end_after=end_after,
        )


__all__ = ["MemoryObservationArchive"]
