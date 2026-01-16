import datetime
from typing import Any

from .portal import Portal
from .task import LcoTask
from ..task import Task
from ..observation import Observation, ObservationState, ObservationList
from ..observationarchive import ObservationArchive


STATE_MAP = {
    "CANCELED": ObservationState.CANCELED,
    "COMPLETED": ObservationState.COMPLETED,
    "PENDING": ObservationState.PENDING,
}


class LcoObservationArchive(ObservationArchive):
    def __init__(self, url: str, token: str, **kwargs: Any):
        """Creates a new LCO observation archive.

        Args:
            url: URL to portal
            token: Authorization token for portal
        """
        ObservationArchive.__init__(self, **kwargs)

        # portal
        self._portal = Portal(url, token)

    async def observations_for_task(self, task: Task) -> ObservationList:
        """Returns list of observations for the given task.

        Args:
            task: Task to get observations for.

        Returns:
            List of observations for the given task.
        """

        if not isinstance(task, LcoTask):
            raise TypeError("Task must be of type LcoTask.")

        portal_observations = await self._portal.observations(task.id)
        observations: list[Observation] = []
        for obs in portal_observations:
            observations.append(
                Observation(
                    id=obs.id,
                    task_id=obs.request,
                    start=obs.start,
                    end=obs.end,
                    state=STATE_MAP[obs.state],
                )
            )
        return ObservationList(observations)

    async def observations_for_night(self, date: datetime.date) -> ObservationList:
        """Returns list of observations for the given task.

        Args:
            date: Date of night to get observations for.

        Returns:
            List of observations for the given task.
        """
        return ObservationList()


__all__ = ["LcoObservationArchive"]
