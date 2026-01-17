from __future__ import annotations
from typing import Any, TYPE_CHECKING
from astropy.time import Time, TimeDelta
import astropy.units as u

from .merit import Merit
from ...observation import ObservationState

if TYPE_CHECKING:
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class IntervalMerit(Merit):
    """Merit function that enforces an interval between observations."""

    def __init__(self, interval: float, **kwargs: Any):
        super().__init__()
        self._interval = interval * u.minute

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        # get all observations for task
        observations = await data.archive.observations_for_task(task)

        # filter for those in the given interval that were successful
        observations = observations.filter(after=time - TimeDelta(self._interval), state=ObservationState.COMPLETED)

        # if there is an observation in the given interval, return 0.0
        return 0.0 if len(observations) > 0 else 1.0


__all__ = ["IntervalMerit"]
