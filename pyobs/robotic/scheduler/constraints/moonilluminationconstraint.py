from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import astroplan
from pydantic import Field

from .constraint import Constraint

if TYPE_CHECKING:
    from pyobs.robotic import Task
    from pyobs.utils.time import Time

    from ..dataprovider import DataProvider


class MoonIlluminationConstraint(Constraint):
    """Maximum Moon illumination (inclusive), ignored when the Moon is below the horizon."""

    cost: float = 3.0
    max_phase: float = Field(ge=0.0, le=1.0, default=0.0)
    req_token: ClassVar[str | None] = "MOONFRAC"

    def req_fields(self) -> dict[str, tuple[int | float | str, str]]:
        return {"MAX": (float(self.max_phase), "fraction")}

    def to_astroplan(self) -> astroplan.MoonIlluminationConstraint:
        return astroplan.MoonIlluminationConstraint(max=self.max_phase)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        if float(data.moon_altaz(time).alt.degree) < 0.0:
            return True
        moon_illumination = data.moon_illumination(time)
        return moon_illumination <= self.max_phase


__all__ = ["MoonIlluminationConstraint"]
