import logging
from typing import Any

from pyobs.interfaces import IRunnable, ITelescope
from pyobs.modules import Module
from pyobs.object import get_object
from pyobs.modules import timeout
from pyobs.robotic.utils.skyflats.pointing import SkyFlatsBasePointing

log = logging.getLogger(__name__)


class FlatFieldPointing(Module, IRunnable):
    """Module for pointing a telescope."""

    __module__ = "pyobs.modules.flatfield"

    def __init__(self, telescope: str | ITelescope, pointing: dict[str, Any] | SkyFlatsBasePointing, **kwargs: Any):
        """Initialize a new flat field pointing.

        Args:
            telescope: Telescope to point
            pointing: Pointing for calculating coordinates.
        """
        Module.__init__(self, **kwargs)

        # store telescope and pointing
        self._telescope = telescope
        self._pointing = pointing

    @timeout(60)
    async def run(self, **kwargs: Any) -> None:
        """Move telescope to pointing."""

        # get telescope
        log.info("Getting proxy for telescope...")
        telescope = await self.proxy(self._telescope, ITelescope)

        # pointing
        pointing = get_object(self._pointing, SkyFlatsBasePointing, observer=self._observer)

        # point
        await pointing(telescope)
        log.info("Finished pointing telescope.")

    async def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        pass


__all__ = ["FlatFieldPointing"]
