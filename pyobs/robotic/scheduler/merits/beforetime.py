from __future__ import annotations
from typing import Any, TYPE_CHECKING
from .merit import Merit

if TYPE_CHECKING:
    from astropy.time import Time
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class BeforeTimeMerit(Merit):
    """Merit function that gives 1 before a given time."""

    def __init__(self, before: Time, **kwargs: Any):
        super().__init__(**kwargs)
        self._before = before

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        return 1.0 if time <= self._before else 0.0


__all__ = ["BeforeTimeMerit"]
