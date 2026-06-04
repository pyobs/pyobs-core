from astropy.time import Time
from pydantic import Field
from typing import TYPE_CHECKING
from astropydantic import AstroPydanticTime  # type: ignore

from .merit import Merit

if TYPE_CHECKING:
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class AfterTimeMerit(Merit):
    """Merit function that gives 1 after a given time."""

    time: AstroPydanticTime = Field(default_factory=Time.now)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        return 1.0 if time >= self.time else 0.0


__all__ = ["AfterTimeMerit"]
