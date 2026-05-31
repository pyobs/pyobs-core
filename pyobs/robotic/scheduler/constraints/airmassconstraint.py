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
        if task.target is None:
            return False
        coord = task.target.coordinates(time)
        altaz = data.observer.altaz(time, coord)
        airmass = float(altaz.secz)
        return 0.0 < airmass <= self.max_airmass and altaz.alt.degree > 0.0


__all__ = ["AirmassConstraint"]
