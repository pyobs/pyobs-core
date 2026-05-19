from __future__ import annotations
from typing import TYPE_CHECKING
import astroplan
import astropy.units as u
import logging

from pydantic import Field

from .constraint import Constraint

if TYPE_CHECKING:
    from astropy.time import Time
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


log = logging.getLogger(__name__)


class SolarElevationConstraint(Constraint):
    """Solar elevation constraint."""

    min_elevation: float = Field(ge=-90, le=90, default=-90.0)
    max_elevation: float = Field(ge=-90, le=90, default=-18.0)

    def to_astroplan(self) -> astroplan.AtNightConstraint:
        if self.min_elevation > -90.0:
            log.warning("Minimum solar elevation constraint not supported by astroplan.")
        return astroplan.AtNightConstraint(max_solar_altitude=self.max_elevation * u.deg)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        sun = data.observer.sun_altaz(time)
        return self.min_elevation <= float(sun.alt.degree) <= self.max_elevation


__all__ = ["SolarElevationConstraint"]
