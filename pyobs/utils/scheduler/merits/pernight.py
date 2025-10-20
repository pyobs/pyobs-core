from typing import Any

from astropy.time import Time

from pyobs.robotic import Task
from ..dataprovider import DataProvider
from ..merit import Merit


class PerNightMerit(Merit):
    """Merit functions for defining a max number of observations per night."""

    def __init__(self, count: int, **kwargs: Any):
        self._count = count

    def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        # get number of successful task runs
        successes = data.get_task_success_count(task)

        # if we have less successful runs than request, merit goes to one
        if successes <= self._count:
            return 1.0

        # get old task run
        ts = data.get_task_success(task, -self._count)
        if ts is None:
            return 1.0

        # if the (-count)th run is not from tonight, we can also run
        if ts.night != data.get_night():
            return 1.0

        # guess, we can't run
        return 0.0


__all__ = ["PerNightMerit"]
