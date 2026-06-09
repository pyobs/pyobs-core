from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyobs.interfaces import IPointingAltAz
from pyobs.robotic.scripts import Script
from pyobs.robotic.utils.skyflats.pointing import SkyFlatsBasePointing

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData

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
        try:
            tel = await self.comm.proxy(self.telescope, IPointingAltAz)
        except ValueError:
            self._cant_run_reason = "No telescope found."
            return False

        if not await tel.is_ready():
            self._cant_run_reason = "Telescope not ready."
            return False

        self._cant_run_reason = None
        return True

    async def run(self, data: TaskData | None) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """
        log.info("Getting proxy for telescope...")
        telescope = await self.comm.proxy(self.telescope, IPointingAltAz)

        await self.pointing(telescope)
        log.info("Finished pointing telescope.")


__all__ = ["PointingScript"]
