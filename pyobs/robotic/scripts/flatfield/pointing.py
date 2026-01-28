from __future__ import annotations
import logging
from typing import Any, TYPE_CHECKING

from pyobs.interfaces import ITelescope
from pyobs.robotic.scripts import Script
from pyobs.utils.skyflats.pointing import SkyFlatsBasePointing

if TYPE_CHECKING:
    from pyobs.robotic import ObservationArchive, TaskArchive, TaskRunner

log = logging.getLogger(__name__)


class Pointing(Script):
    """Script for pointing the telescope for flats."""

    def __init__(
        self,
        telescope: str | ITelescope,
        pointing: dict[str, Any] | SkyFlatsBasePointing,
        **kwargs: Any,
    ):
        """Init a new Pointing script.
        Args:
            telescope: telescope to move.
            pointing: pointing class to use.
        """
        if "configuration" not in kwargs:
            kwargs["configuration"] = {}
        Script.__init__(self, **kwargs)

        # store modules
        self._telescope = telescope
        self._pointing = self.get_object(pointing)

    async def can_run(self) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """

        # get modules
        try:
            tel = await self.comm.proxy(self._telescope, ITelescope)
        except ValueError:
            return False

        # we need a camera
        if not await tel.is_ready():
            return False

        # seems alright
        return True

    async def run(
        self,
        task_runner: TaskRunner | None = None,
        observation_archive: ObservationArchive | None = None,
        task_archive: TaskArchive | None = None,
    ) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """
        # get modules
        log.info("Getting proxy for telescope...")
        telescope = await self.comm.proxy(self._telescope, ITelescope)

        # point
        await self._pointing(telescope)
        log.info("Finished pointing telescope.")


__all__ = ["Pointing"]
