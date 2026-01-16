from __future__ import annotations
from typing import Any, TYPE_CHECKING
import astroplan
from .constraint import Constraint

if TYPE_CHECKING:
    from astropy.time import Time
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


class AirmassConstraint(Constraint):
    """Airmass constraint."""

    def __init__(self, max_airmass: float, **kwargs: Any):
        super().__init__()
        self.max_airmass = max_airmass

    def to_astroplan(self) -> astroplan.AirmassConstraint:
        return astroplan.AirmassConstraint(max=self.max_airmass)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        airmass = float(data.observer.altaz(time, task.target).secz)
        return 0.0 < airmass <= self.max_airmass


__all__ = ["AirmassConstraint"]
