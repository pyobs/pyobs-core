from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Self
from astropy.time import Time, TimeDelta
import astropy.units as u
from pydantic import Field, model_validator, PrivateAttr

from .merit import Merit

if TYPE_CHECKING:
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


TimeUnit = Literal["s", "min", "h", "hr", "d", "yr"]


class IntervalMerit(Merit):
    """Merit function that enforces an interval between observations."""

    interval: float = Field(ge=0.0, le=31536000.0, default=0.0)
    unit: Literal["s", "min", "h", "hr", "d", "wk", "yr"] = "s"

    _interval: TimeDelta = PrivateAttr()

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def calculate_derived(self) -> Self:
        self._interval = TimeDelta(self.interval * u.Unit(self.unit))
        return self

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        from ...observation import ObservationState

        # get completed observations for task within the interval
        observations = await data.archive.get_observations(
            task=task,
            state=ObservationState.COMPLETED,
            start_after=time - self._interval,
        )

        # if there is an observation in the given interval, return 0.0
        return 0.0 if len(observations) > 0 else 1.0


__all__ = ["IntervalMerit"]
