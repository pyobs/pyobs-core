from __future__ import annotations
from typing import Any, TYPE_CHECKING
import astroplan
import astropy.units as u
import astropy.coordinates
from .constraint import Constraint

if TYPE_CHECKING:
    from astropy.time import Time
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


class MoonSeparationConstraint(Constraint):
    """Moon separation constraint."""

    def __init__(self, min_distance: float, **kwargs: Any):
        super().__init__(**kwargs)
        self.min_distance = min_distance

    def to_astroplan(self) -> astroplan.MoonSeparationConstraint:
        return astroplan.MoonSeparationConstraint(min=self.min_distance * u.deg)

    def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        target = task.target
        if target is None:
            return True
        moon_separation = astropy.coordinates.get_body("moon", time).separation(
            target.coordinates(time), origin_mismatch="ignore"
        )
        return float(moon_separation.degree) >= self.min_distance


__all__ = ["MoonSeparationConstraint"]
