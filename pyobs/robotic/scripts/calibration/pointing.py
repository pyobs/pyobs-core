from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyobs.interfaces import IPointingAltAz, IReady
from pyobs.robotic.scripts import Script
from pyobs.robotic.utils.skyflats.pointing import SkyFlatsBasePointing

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
    from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class PointingScript(Script):
    """Script for pointing the telescope for flats."""

    telescope: str
    pointing: SkyFlatsBasePointing

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """
        if not await self.comm.has_proxy(self.telescope, IPointingAltAz):
            self._cant_run_reason = "No telescope found."
            return False

        async with self.comm.proxy(self.telescope, IReady) as telescope:
            if not await telescope.is_ready():
                self._cant_run_reason = "Telescope not ready."
                return False

        self._cant_run_reason = None
        return True

    async def run(self, data: TaskData | None) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """
        async with self.comm.proxy(self.telescope, IPointingAltAz) as telescope:
            await self.pointing(telescope)
            log.info("Finished pointing telescope.")

    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        """Estimate duration of slewing to the flat-field pointing."""
        # TODO: get a better estimate for slewing
        return 60.0


__all__ = ["PointingScript"]
