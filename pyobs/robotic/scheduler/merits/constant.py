from __future__ import annotations
from typing import TYPE_CHECKING
from .merit import Merit

if TYPE_CHECKING:
    from astropy.time import Time
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class ConstantMerit(Merit):
    """Merit function that returns a constant value."""

    merit: float

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        return self.merit


__all__ = ["ConstantMerit"]
