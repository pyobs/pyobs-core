from __future__ import annotations
from typing import TYPE_CHECKING
import astroplan
from astropydantic import AstroPydanticTime  # type: ignore

from .constraint import Constraint

if TYPE_CHECKING:
    from astropy.time import Time
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


class TimeConstraint(Constraint):
    """Time constraint."""

    start: AstroPydanticTime
    end: AstroPydanticTime

    def to_astroplan(self) -> astroplan.TimeConstraint:
        return astroplan.TimeConstraint(min=self.start, max=self.end)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        return bool(self.start <= time <= self.end)


__all__ = ["TimeConstraint"]
