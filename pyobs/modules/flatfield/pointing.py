from __future__ import annotations

import logging
from typing import Any

from pyobs.interfaces import IPointingAltAz, IRunnable
from pyobs.modules import Module, timeout
from pyobs.object import get_object
from pyobs.robotic.utils.skyflats.pointing import SkyFlatsBasePointing

log = logging.getLogger(__name__)


class FlatFieldPointing(Module, IRunnable):
    """Module for pointing a telescope."""

    __module__ = "pyobs.modules.flatfield"

    def __init__(self, telescope: str | IPointingAltAz, pointing: dict[str, Any] | SkyFlatsBasePointing, **kwargs: Any):
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

        pointing = get_object(self._pointing, SkyFlatsBasePointing, observer=self._observer)
        async with self.proxy(self._telescope, IPointingAltAz) as proxy:
            log.info("Pointing telescope...")
            await pointing(proxy)
        log.info("Finished pointing telescope.")

    async def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        pass


__all__ = ["FlatFieldPointing"]
