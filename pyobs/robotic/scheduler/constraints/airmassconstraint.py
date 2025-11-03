from typing import Any
import astroplan

from .constraint import Constraint


class AirmassConstraint(Constraint):
    """Airmass constraint."""

    def __init__(self, max_airmass: float, **kwargs: Any):
        super().__init__(**kwargs)
        self.max_airmass = max_airmass

    def to_astroplan(self) -> astroplan.AirmassConstraint:
        return astroplan.AirmassConstraint(max=self.max_airmass)


__all__ = ["AirmassConstraint"]
