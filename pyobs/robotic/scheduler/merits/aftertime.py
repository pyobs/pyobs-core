from __future__ import annotations
from typing import Any, TYPE_CHECKING
from .merit import Merit

if TYPE_CHECKING:
    from astropy.time import Time
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class AfterTimeMerit(Merit):
    """Merit function that gives 1 after a given time."""

    def __init__(self, after: Time, **kwargs: Any):
        super().__init__()
        self._after = after

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        return 1.0 if time >= self._after else 0.0


__all__ = ["AfterTimeMerit"]
