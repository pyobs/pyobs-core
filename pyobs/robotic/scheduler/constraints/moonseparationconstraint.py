from __future__ import annotations
from typing import TYPE_CHECKING
import astroplan
import astropy.units as u
import astropy.coordinates
from pydantic import Field

from .constraint import Constraint

if TYPE_CHECKING:
    from astropy.time import Time
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


class MoonSeparationConstraint(Constraint):
    """Moon separation constraint."""

    cost: float = 3.0
    min_distance: float = Field(ge=0.0, le=180.0, default=30.0)

    def to_astroplan(self) -> astroplan.MoonSeparationConstraint:
        return astroplan.MoonSeparationConstraint(min=self.min_distance * u.deg)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        if task.target is None:
            return True
        coord = task.target.coordinates(time)
        moon_separation = astropy.coordinates.get_body("moon", time).separation(coord, origin_mismatch="ignore")
        return float(moon_separation.degree) >= self.min_distance


__all__ = ["MoonSeparationConstraint"]
