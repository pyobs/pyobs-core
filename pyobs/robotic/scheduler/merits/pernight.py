from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from .merit import Merit

if TYPE_CHECKING:
    from pyobs.robotic import Task
    from pyobs.utils.time import Time

    from ..dataprovider import DataProvider


class PerNightMerit(Merit):
    """Merit functions for defining a max number of observations per observing period."""

    count: int = Field(ge=0, le=999, default=0)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        from ...observation import ObservationState

        # get completed observations for task in the selected history cycle
        observations = await data.archive.observations_for_task(task=task)
        start, end = data.period_bounds(time)
        observations = observations.filter(state=ObservationState.COMPLETED, start_after=start)
        count = sum(1 for obs in observations if obs.start < end)

        # compare to count
        return 1.0 if count < self.count else 0.0


__all__ = ["PerNightMerit"]
