from typing import Any, TYPE_CHECKING
from astropy.coordinates import SkyCoord
from pydantic import PrivateAttr, Field

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

    def _get_picker(self) -> Picker:
        return self.pyobs_model_validate(Picker, self._picker, by_alias=True)

    async def resolve(self, time: Time, task: Task, data: DataProvider) -> None:
        """Pick the best available target given current conditions. For static targets this will just be itself."""
        from .picker import Picker

        picker = self._get_picker()
        self._target = await picker(time, task, data)
        self.name = self._target.name if self._target is not None else "None"

    def coordinates(self, time: Time) -> SkyCoord:
        if self._target is None:
            raise RuntimeError("Target not resolved yet.")
        return self._target.coordinates(time)


__all__ = ["DynamicTarget"]
