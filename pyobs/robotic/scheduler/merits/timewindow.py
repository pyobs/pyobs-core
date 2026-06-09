from __future__ import annotations

from typing import TYPE_CHECKING

from astropydantic import AstroPydanticTime  # type: ignore
from pydantic import Field

from pyobs.utils.serialization import BaseModel
from pyobs.utils.time import Time

from .merit import Merit

if TYPE_CHECKING:
    from pyobs.robotic import Task

    from ..dataprovider import DataProvider


class TimeWindow(BaseModel):
    start: AstroPydanticTime = Field(default_factory=Time.now)
    end: AstroPydanticTime = Field(default_factory=Time.now)


class TimeWindowMerit(Merit):
    """Merit function that uses time windows."""

    windows: list[TimeWindow] = Field(default_factory=list)
    inverse: bool = False

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> float:
        # is time in any of the windows?
        in_window = False
        for window in self.windows:
            if window.start <= time <= window.end:
                in_window = True

        # invert?
        if not self.inverse:
            return 1.0 if in_window else 0.0
        else:
            return 0.0 if in_window else 1.0


__all__ = ["TimeWindowMerit", "TimeWindow"]
