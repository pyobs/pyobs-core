from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any, Self

from pydantic import model_validator, ConfigDict

from pyobs.interfaces import IBinning, ICamera, IWindow, IExposureTime, IImageType, IData, IAutoFocus
from pyobs.robotic.scripts import Script
from pyobs.utils.enums import ImageType
from pyobs.utils.targetpicker import TargetPicker

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData

log = logging.getLogger(__name__)


class AutoFocus(Script):
    """Script for running autofocus series."""

    autofocus: str = "autofocus"
    target: TargetPicker | dict[str, Any] | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def create_target_picker(self) -> Self:
        if isinstance(self.target, dict):
            self.target = self.get_object(self.target, TargetPicker)
        return self

    async def can_run(self, data: TaskData) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """

        # we need a camera
        try:
            await Script._comm(data).proxy(self.autofocus, IAutoFocus)
        except ValueError:
            return False

        # seems alright
        return isinstance(self.target, TargetPicker)

    async def run(self, data: TaskData) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """

        if not isinstance(self.target, TargetPicker):
            return

        target = await self.target(data.vfs, data.observer)
        print(target)


__all__ = ["AutoFocus"]
