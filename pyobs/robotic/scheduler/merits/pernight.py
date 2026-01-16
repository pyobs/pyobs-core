from __future__ import annotations
from typing import Any, TYPE_CHECKING
from .merit import Merit
from ...observation import ObservationState

if TYPE_CHECKING:
    from astropy.time import Time
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class PerNightMerit(Merit):
    """Merit functions for defining a max number of observations per night."""

    def __init__(self, count: int, **kwargs: Any):
        super().__init__()
        self._count = count

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        # get all observations for task
        observations = await data.archive.observations_for_task(task)

        # filter for those after last sunset that were successful
        observations = observations.filter(after=data.last_sunset(time), state=ObservationState.COMPLETED)

        # compare to count
        return 1.0 if len(observations) <= self._count else 0.0


__all__ = ["PerNightMerit"]
