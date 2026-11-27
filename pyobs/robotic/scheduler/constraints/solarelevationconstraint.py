from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

import astroplan
import astropy.units as u
from pydantic import Field

from pyobs.utils.time import Time

from .constraint import Constraint, stricter

if TYPE_CHECKING:
    from pyobs.robotic import Task

    from ..dataprovider import DataProvider


log = logging.getLogger(__name__)


class SolarElevationConstraint(Constraint):
    """Solar elevation constraint."""

    min_elevation: float = Field(ge=-90, le=90, default=-90.0, json_schema_extra=stricter("higher"))
    max_elevation: float = Field(ge=-90, le=90, default=-18.0, json_schema_extra=stricter("lower"))
    req_token: ClassVar[str | None] = "SUNALT"

    def req_fields(self) -> dict[str, tuple[int | float | str, str]]:
        fields: dict[str, tuple[int | float | str, str]] = {}
        if self.min_elevation > -90.0:
            fields["MIN"] = (float(self.min_elevation), "deg")
        if self.max_elevation < 90.0:
            fields["MAX"] = (float(self.max_elevation), "deg")
        return fields

    def to_astroplan(self) -> astroplan.AtNightConstraint:
        if self.min_elevation > -90.0:
            log.warning("Minimum solar elevation constraint not supported by astroplan.")
        return astroplan.AtNightConstraint(max_solar_altitude=self.max_elevation * u.deg)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        sun = data.sun_altaz(time)
        return self.min_elevation <= float(sun.alt.degree) <= self.max_elevation


__all__ = ["SolarElevationConstraint"]
