from typing import Any
import astroplan

from .constraint import Constraint


class MoonSeparationConstraint(Constraint):
    """Moon separation constraint."""

    def __init__(self, min_distance: float, **kwargs: Any):
        super().__init__(**kwargs)
        self.min_distance = min_distance

    def to_astroplan(self) -> astroplan.MoonSeparationConstraint:
        return astroplan.MoonSeparationConstraint(min=self.min_distance)


__all__ = ["MoonSeparationConstraint"]
