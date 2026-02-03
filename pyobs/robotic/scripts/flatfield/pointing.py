from __future__ import annotations
import logging
from typing import Any, TYPE_CHECKING

from pyobs.interfaces import IPointingAltAz
from pyobs.object import get_object
from pyobs.robotic.scripts import Script

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData

log = logging.getLogger(__name__)


class Pointing(Script):
    """Script for pointing the telescope for flats."""

    telescope: str
    pointing: dict[str, Any]

    async def can_run(self, data: TaskData) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """

        # get modules
        try:
            tel = await self.__comm(data).proxy(self.telescope, IPointingAltAz)
        except ValueError:
            return False

        # we need a camera
        if not await tel.is_ready():
            return False

        # seems alright
        return True

    async def run(self, data: TaskData) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """
        # get modules
        log.info("Getting proxy for telescope...")
        telescope = await self.__comm(data).proxy(self.telescope, IPointingAltAz)

        # point
        pointing = get_object(self.pointing)
        await pointing(telescope)
        log.info("Finished pointing telescope.")


__all__ = ["Pointing"]
