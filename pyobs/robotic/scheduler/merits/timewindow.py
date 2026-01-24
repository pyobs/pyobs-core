from __future__ import annotations
from typing import Any, TYPE_CHECKING, TypedDict
from .merit import Merit

if TYPE_CHECKING:
    from astropy.time import Time
    from pyobs.robotic import Task
    from ..dataprovider import DataProvider


class TimeWindow(TypedDict):
    start: str
    end: int


class TimeWindowMerit(Merit):
    """Merit function that uses time windows."""

    def __init__(self, windows: list[TimeWindow], inverse: bool = False, **kwargs: Any):
        super().__init__()
        self._windows = windows
        self._inverse = inverse

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        # is time in any of the windows?
        in_window = False
        for window in self._windows:
            if window["start"] <= time <= window["end"]:
                in_window = True

        # invert?
        if not self._inverse:
            return 1.0 if in_window else 0.0
        else:
            return 0.0 if in_window else 1.0


__all__ = ["TimeWindowMerit"]
