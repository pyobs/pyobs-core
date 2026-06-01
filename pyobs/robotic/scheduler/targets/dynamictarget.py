from typing import Any, TYPE_CHECKING
from astropy.coordinates import SkyCoord
from pydantic import PrivateAttr, Field, ConfigDict

from pyobs.utils.time import Time
from .target import Target

if TYPE_CHECKING:
    from .picker import Picker
    from pyobs.robotic import Task
    from pyobs.robotic.scheduler import DataProvider


class DynamicTarget(Target):
    picker: dict[str, Any] = Field(default_factory=dict)

    _target: Target | None = PrivateAttr(default=None)
    _picker: Picker | None = PrivateAttr(default=None)

    model_config = ConfigDict(frozen=False)

    def _get_picker(self) -> Picker | None:
        if self._picker is None:
            self._picker = self.pyobs_model_validate(Picker, self.picker, by_alias=True)
        return self._picker

    async def resolve(self, time: Time, task: Task, data: DataProvider) -> None:
        """Pick the best available target given current conditions. For static targets this will just be itself."""
        picker = self._get_picker()
        if picker is not None:
            self._target = await picker(time, task, data)
        self.name = self._target.name if self._target is not None else "None"

    def coordinates(self, time: Time) -> SkyCoord:
        if self._target is None:
            raise RuntimeError("Target not resolved yet.")
        return self._target.coordinates(time)


__all__ = ["DynamicTarget"]
