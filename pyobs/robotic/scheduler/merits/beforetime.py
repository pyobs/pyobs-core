from __future__ import annotations
from typing import TYPE_CHECKING

from astropydantic import AstroPydanticTime

from .merit import Merit

if TYPE_CHECKING:
    from astropy.time import Time
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class BeforeTimeMerit(Merit):
    """Merit function that gives 1 before a given time."""

    time: AstroPydanticTime

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        return 1.0 if time <= self.time else 0.0


__all__ = ["BeforeTimeMerit"]
