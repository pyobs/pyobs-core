from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

import astroplan
import astropy.units as u
from astropy.coordinates import get_sun
from pydantic import Field

from pyobs.utils.time import Time

from .constraint import Constraint

if TYPE_CHECKING:
    from pyobs.robotic import Task

    from ..dataprovider import DataProvider


log = logging.getLogger(__name__)


class SolarElevationConstraint(Constraint):
    """Solar elevation constraint."""

    min_elevation: float = Field(ge=-90, le=90, default=-90.0)
    max_elevation: float = Field(ge=-90, le=90, default=-18.0)
    direction: Literal["rising", "setting", "both"] = "both"

    def to_astroplan(self) -> astroplan.AtNightConstraint:
        if self.min_elevation > -90.0:
            log.warning("Minimum solar elevation constraint not supported by astroplan.")
        return astroplan.AtNightConstraint(max_solar_altitude=self.max_elevation * u.deg)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        sun = data.observer.sun_altaz(time)
        in_range = self.min_elevation <= float(sun.alt.degree) <= self.max_elevation
        if self.direction == "both":
            return in_range
        else:
            sun_coord = get_sun(time)
            transit = data.observer.target_meridian_transit_time(time, sun_coord, which="nearest")
            midnight = data.observer.midnight(time, which="nearest")

            if self.direction == "rising":
                return in_range and bool(midnight < time < transit)
            else:
                return in_range and not bool(midnight < time < transit)


__all__ = ["SolarElevationConstraint"]
