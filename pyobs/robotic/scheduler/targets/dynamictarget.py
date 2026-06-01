from astroplan import Observer
from typing import Self, Any
from astropy.coordinates import SkyCoord
from pydantic import model_validator, PrivateAttr, Field

from pyobs.utils.time import Time
from .target import Target


class DynamicTarget(Target):
    picker: dict[str, Any] = Field(default_factory=dict)

    _target: Target | None = PrivateAttr(default=None)

    async def resolve(self, time: Time, observer: Observer) -> None:
        """Pick the best available target given current conditions. For static targets this will just be itself."""
        from .picker import Picker

        picker = self.pyobs_model_validate(Picker, self.picker)

    def coordinates(self, time: Time) -> SkyCoord:
        if self._target is None:
            raise RuntimeError("Target not resolved yet.")
        return self._target.coordinates(time)


__all__ = ["DynamicTarget"]
