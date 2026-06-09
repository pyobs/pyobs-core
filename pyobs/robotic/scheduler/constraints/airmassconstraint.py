from __future__ import annotations

from typing import TYPE_CHECKING

import astroplan
import numpy as np
from astropy.coordinates import SkyCoord
from pydantic import Field

from .constraint import Constraint

if TYPE_CHECKING:
    from pyobs.robotic import Task
    from pyobs.utils.time import Time

    from ..dataprovider import DataProvider


class AirmassConstraint(Constraint):
    """Airmass constraint."""

    cost: float = 2.0
    target_dependent: bool = True
    max_airmass: float = Field(ge=1.0, le=9.9, default=1.3)

    def to_astroplan(self) -> astroplan.AirmassConstraint:
        return astroplan.AirmassConstraint(max=self.max_airmass)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        if task.target is None:
            return False
        coord = task.target.coordinates(time)
        altaz = data.observer.altaz(time, coord)
        airmass = float(altaz.secz)
        return bool(0.0 < airmass <= self.max_airmass and altaz.alt.degree > 0.0)

    async def filter_skycoord(self, time: Time, coords: SkyCoord, data: DataProvider) -> np.ndarray:
        altaz = data.observer.altaz(time, coords)
        return np.asarray((altaz.secz > 0.0) & (altaz.secz <= self.max_airmass) & (altaz.alt.deg > 0.0), dtype=np.bool_)


__all__ = ["AirmassConstraint"]
