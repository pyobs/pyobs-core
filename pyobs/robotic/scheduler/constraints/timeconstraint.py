from __future__ import annotations
from typing import TYPE_CHECKING
import astroplan
from astropydantic import AstroPydanticTime  # type: ignore
from pydantic import Field
from astropy.time import Time

from .constraint import Constraint

if TYPE_CHECKING:
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


class TimeConstraint(Constraint):
    """Time constraint."""

    start: AstroPydanticTime = Field(default_factory=Time.now)
    end: AstroPydanticTime = Field(default_factory=Time.now)

    def to_astroplan(self) -> astroplan.TimeConstraint:
        return astroplan.TimeConstraint(min=self.start, max=self.end)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        return bool(self.start <= time <= self.end)


__all__ = ["TimeConstraint"]
