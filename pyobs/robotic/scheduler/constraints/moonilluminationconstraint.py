from __future__ import annotations
from typing import Any, TYPE_CHECKING
import astroplan
from .constraint import Constraint

if TYPE_CHECKING:
    from astropy.time import Time
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


class MoonIlluminationConstraint(Constraint):
    """Moon illumination constraint."""

    def __init__(self, max_phase: float, **kwargs: Any):
        super().__init__()
        self.max_phase = max_phase

    def to_astroplan(self) -> astroplan.MoonIlluminationConstraint:
        return astroplan.MoonIlluminationConstraint(max=self.max_phase)

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        moon_illumination = float(data.observer.moon_illumination(time))
        return moon_illumination <= self.max_phase


__all__ = ["MoonIlluminationConstraint"]
