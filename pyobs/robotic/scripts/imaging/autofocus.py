from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyobs.interfaces import IAutoFocus, IMotion, IPointingRaDec, ITelescope
from pyobs.robotic.scripts import Script
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData

log = logging.getLogger(__name__)


class AutoFocusScript(Script):
    """Script for running autofocus series."""

    autofocus: str = "autofocus"
    telescope: str = "telescope"
    count: int = 5
    step: float = 0.1
    exposure_time: float = 2.0

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """

        # we need a camera
        try:
            await self.comm.proxy(self.autofocus, IAutoFocus)
        except ValueError:
            self._cant_run_reason = "No autofocus found."
            return False
        try:
            telescope = await self.comm.proxy(self.telescope, IPointingRaDec)
        except ValueError:
            self._cant_run_reason = "No telescope found."
            return False

        # ready?
        if not isinstance(telescope, ITelescope):
            self._cant_run_reason = "No ITelescope found."
            return False
        if not await telescope.is_ready():
            self._cant_run_reason = "Telescope not ready."
            return False

        # all good
        self._cant_run_reason = None
        return True

    async def run(self, data: TaskData | None) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """
        if data is None or data.task is None:
            return

        autofocus = await self.comm.proxy(self.autofocus, IAutoFocus)
        telescope = await self.comm.proxy(self.telescope, IPointingRaDec)

        target = data.task.target
        if target is None:
            raise ValueError("No target given.")
        log.info("Picked target %s for auto focus...", target)

        log.info("Moving telescope...")
        coord = target.coordinates(Time.now())
        await telescope.move_radec(coord.ra.degree, coord.dec.degree)

        try:
            log.info("Performing auto focus...")
            await autofocus.auto_focus(self.count, self.step, self.exposure_time)

        finally:
            if isinstance(telescope, IMotion):
                log.info("Stopping telescope...")
                await telescope.stop_motion()
            log.info("Done.")

    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        """Estimate duration of the autofocus run."""
        # TODO: get a better estimate for slewing
        return self.count * self.exposure_time + 60.0


__all__ = ["AutoFocusScript"]
