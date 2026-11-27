from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

import astroplan
import astropy.units as u
from pydantic import Field, field_validator

from pyobs.utils.time import Time

from .constraint import Constraint, stricter

if TYPE_CHECKING:
    from pyobs.robotic import Task

    from ..dataprovider import DataProvider


log = logging.getLogger(__name__)


class SolarElevationConstraint(Constraint):
    """Solar elevation constraint.

    Usually only one limit is needed, e.g. `max_elevation=-18` for astronomical night. A limit of
    None (or -90/90, which are normalised to None) means no limit on that side.
    """

    min_elevation: float | None = Field(ge=-90, le=90, default=None, json_schema_extra=stricter("higher"))
    max_elevation: float | None = Field(ge=-90, le=90, default=-18.0, json_schema_extra=stricter("lower"))
    req_token: ClassVar[str | None] = "SUNALT"

    @field_validator("min_elevation")
    @classmethod
    def _no_min_limit(cls, value: float | None) -> float | None:
        return None if value is not None and value <= -90.0 else value

    @field_validator("max_elevation")
    @classmethod
    def _no_max_limit(cls, value: float | None) -> float | None:
        return None if value is not None and value >= 90.0 else value

    def req_fields(self) -> dict[str, tuple[int | float | str, str]]:
        fields: dict[str, tuple[int | float | str, str]] = {}
        if self.min_elevation is not None:
            fields["MIN"] = (float(self.min_elevation), "deg")
        if self.max_elevation is not None:
            fields["MAX"] = (float(self.max_elevation), "deg")
        return fields

    def to_astroplan(self) -> astroplan.AtNightConstraint:
        if self.min_elevation is not None:
            log.warning("Minimum solar elevation constraint not supported by astroplan.")
        max_elevation = 90.0 if self.max_elevation is None else self.max_elevation
        return astroplan.AtNightConstraint(max_solar_altitude=max_elevation * u.deg)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        alt = float(data.sun_altaz(time).alt.degree)
        if self.min_elevation is not None and alt < self.min_elevation:
            return False
        return self.max_elevation is None or alt <= self.max_elevation


__all__ = ["SolarElevationConstraint"]
