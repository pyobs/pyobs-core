from __future__ import annotations
from typing import TYPE_CHECKING
import astroplan
import astropy.units as u
from .constraint import Constraint

if TYPE_CHECKING:
    from astropy.time import Time
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


class SolarElevationConstraint(Constraint):
    """Solar elevation constraint."""

    max_elevation: float

    def to_astroplan(self) -> astroplan.AtNightConstraint:
        return astroplan.AtNightConstraint(max_solar_altitude=self.max_elevation * u.deg)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        sun = data.observer.sun_altaz(time)
        return float(sun.alt.degree) <= self.max_elevation


__all__ = ["SolarElevationConstraint"]
