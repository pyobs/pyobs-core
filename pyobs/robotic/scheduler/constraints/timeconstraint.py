from __future__ import annotations
from typing import Any, TYPE_CHECKING
import astroplan
from .constraint import Constraint

if TYPE_CHECKING:
    from astropy.time import Time
    from ..dataprovider import DataProvider
    from pyobs.robotic import Task


class TimeConstraint(Constraint):
    """Time constraint."""

    def __init__(self, start: Time, end: Time, **kwargs: Any):
        super().__init__(**kwargs)
        self.start = start
        self.end = end

    def to_astroplan(self) -> astroplan.TimeConstraint:
        return astroplan.TimeConstraint(min=self.start, max=self.end)

    def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        return bool(self.start <= time <= self.end)


__all__ = ["TimeConstraint"]
