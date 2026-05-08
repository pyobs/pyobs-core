from __future__ import annotations
from typing import TYPE_CHECKING
import astroplan
from pydantic import Field

from .constraint import Constraint

if TYPE_CHECKING:
    from astropy.time import Time
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


class AirmassConstraint(Constraint):
    """Airmass constraint."""

    max_airmass: float = Field(ge=1.0, le=9.9, default=1.3)

    def to_astroplan(self) -> astroplan.AirmassConstraint:
        return astroplan.AirmassConstraint(max=self.max_airmass)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        airmass = float(data.observer.altaz(time, task.target).secz)
        return 0.0 < airmass <= self.max_airmass


__all__ = ["AirmassConstraint"]
