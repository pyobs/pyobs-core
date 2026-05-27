from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from pyobs.interfaces import IAutoFocus, IPointingRaDec, ITelescope
from pyobs.robotic.scripts import Script
from pyobs.robotic.utils.targetpicker import TargetPicker

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData

log = logging.getLogger(__name__)


class AutoFocus(Script):
    """Script for running autofocus series."""

    autofocus: str = "autofocus"
    telescope: str = "telescope"
    count: int = 5
    step: float = 0.1
    exposure_time: float = 2.0
    target: TargetPicker | None = None

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """

        # we need a camera
        try:
            await self.comm.proxy(self.autofocus, IAutoFocus)
            telescope = await self.comm.proxy(self.telescope, IPointingRaDec)
        except ValueError:
            return False

        # ready?
        if not isinstance(telescope, ITelescope):
            return False
        return await telescope.is_ready()

    async def run(self, data: TaskData | None) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """

        if not isinstance(self.target, TargetPicker):
            return

        autofocus = await self.comm.proxy(self.autofocus, IAutoFocus)
        telescope = await self.comm.proxy(self.telescope, IPointingRaDec)

        name, target = await self.target()
        log.info(f"Picked target '{name}' at coordinates {target.to_string()} for auto focus...")

        log.info("Moving telescope...")
        await telescope.move_radec(target.ra.degree, target.dec.degree)

        log.info("Performing auto focus...")
        await autofocus.auto_focus(self.count, self.step, self.exposure_time)
        log.info("Done.")


__all__ = ["AutoFocus"]
