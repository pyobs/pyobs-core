from __future__ import annotations
from typing import Any, TYPE_CHECKING
from .merit import Merit
from ...observation import ObservationState

if TYPE_CHECKING:
    from astropy.time import Time
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class FollowMerit(Merit):
    """Merit functions that only returns after another given task has run this night."""

    task_id: Any

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        # get all observations for tonight
        night = data.night(time)
        observations = await data.archive.observations_for_night(night)

        # filter for successful ones of the given task
        observations = observations.filter(task_id=self.task_id, state=ObservationState.COMPLETED)

        # compare to count
        return 1.0 if len(observations) > 0 else 0.0


__all__ = ["FollowMerit"]
