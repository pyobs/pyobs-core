from enum import StrEnum  # type: ignore
from typing import Any
import astroplan

from .constraint import Constraint


class MoonCondition(StrEnum):  # type: ignore
    """Represents a moon condition."""

    DARK = "dark"
    GREY = "grey"
    BRIGHT = "bright"


class MoonConstraint(Constraint):
    """Airmass constraint."""

    def __init__(self, moon: MoonCondition, **kwargs: Any):
        super().__init__(**kwargs)
        self.moon = moon

    def to_astroplan(self) -> astroplan.Constraint:
        raise NotImplementedError()


__all__ = ["MoonCondition", "MoonConstraint"]
