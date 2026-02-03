from __future__ import annotations
from typing import TYPE_CHECKING
from .merit import Merit

if TYPE_CHECKING:
    from astropy.time import Time
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class PerNightMerit(Merit):
    """Merit functions for defining a max number of observations per night."""

    count: int

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        from ...observation import ObservationState

        # get all observations for task
        observations = await data.archive.observations_for_task(task)

        # filter for those after last sunset that were successful
        observations = observations.filter(after=data.last_sunrise(time), state=ObservationState.COMPLETED)

        # compare to count
        return 1.0 if len(observations) < self.count else 0.0


__all__ = ["PerNightMerit"]
