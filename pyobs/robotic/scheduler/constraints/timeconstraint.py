from typing import Any
import astroplan

from pyobs.utils.time import Time
from .constraint import Constraint


class TimeConstraint(Constraint):
    """Time constraint."""

    def __init__(self, start: Time, end: Time, **kwargs: Any):
        super().__init__(**kwargs)
        self.start = start
        self.end = end

    def to_astroplan(self) -> astroplan.TimeConstraint:
        return astroplan.TimeConstraint(min=self.start, max=self.end)


__all__ = ["TimeConstraint"]
