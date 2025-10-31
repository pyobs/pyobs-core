from typing import Any
import astroplan

from .constraint import Constraint


class SolarElevationConstraint(Constraint):
    """Solar elevation constraint."""

    def __init__(self, max_elevation: float, **kwargs: Any):
        super().__init__(**kwargs)
        self.max_elevation = max_elevation

    def to_astroplan(self) -> astroplan.AtNightConstraint:
        return astroplan.AtNightConstraint(max_solar_altitude=self.max_elevation)


__all__ = ["SolarElevationConstraint"]
