from __future__ import annotations
from typing import TYPE_CHECKING

from pydantic import Field

from .merit import Merit

if TYPE_CHECKING:
    from astropy.time import Time
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class PerNightMerit(Merit):
    """Merit functions for defining a max number of observations per night."""

    count: int = Field(ge=0, le=999, default=0)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        from ...observation import ObservationState

        # get completed observations for task since last sunrise
        observations = await data.archive.observations_for_task(task=task)
        observations = observations.filter(state=ObservationState.COMPLETED, start_after=data.last_sunrise(time))

        # compare to count
        return 1.0 if len(observations) < self.count else 0.0


__all__ = ["PerNightMerit"]
