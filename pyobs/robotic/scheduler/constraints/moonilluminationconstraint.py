from typing import Any

import astroplan

from .constraint import Constraint


class MoonIlluminationConstraint(Constraint):
    """Moon illumination constraint."""

    def __init__(self, max_phase: float, **kwargs: Any):
        super().__init__(**kwargs)
        self.max_phase = max_phase

    def to_astroplan(self) -> astroplan.MoonIlluminationConstraint:
        return astroplan.MoonIlluminationConstraint(max=self.max_phase)


__all__ = ["MoonIlluminationConstraint"]
