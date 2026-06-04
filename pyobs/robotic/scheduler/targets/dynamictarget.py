from __future__ import annotations

from typing import TYPE_CHECKING

from astropy.coordinates import SkyCoord
from pydantic import ConfigDict, PrivateAttr

from pyobs.utils.time import Time

from .picker import Picker
from .target import Target

if TYPE_CHECKING:
    from pyobs.robotic import Task
    from pyobs.robotic.scheduler import DataProvider


class DynamicTarget(Target):
    picker: Picker
    name: str = "(dynamic)"

    _target: Target | None = PrivateAttr(default=None)

    model_config = ConfigDict(frozen=False)

    async def resolve(self, time: Time, task: Task, data: DataProvider) -> Target | None:
        """Pick the best available target given current conditions. For static targets this will just be itself."""
        self._target = await self.picker(time, task, data)
        self.name = self._target.name if self._target is not None else "None"
        return self._target

    def coordinates(self, time: Time) -> SkyCoord:
        if self._target is None:
            raise RuntimeError("Target not resolved yet.")
        return self._target.coordinates(time)

    def __str__(self) -> str:
        return "dynamic" if self._target is None else str(self._target)


__all__ = ["DynamicTarget"]
