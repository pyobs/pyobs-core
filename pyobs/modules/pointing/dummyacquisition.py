import asyncio
import logging
from typing import Any, Dict

from pyobs.interfaces import IAcquisition
from pyobs.modules import Module
from pyobs.modules import timeout

log = logging.getLogger(__name__)


class DummyAcquisition(Module, IAcquisition):
    """Dummy class for telescope acquisition."""

    __module__ = "pyobs.modules.acquisition"

    def __init__(self, wait_secs: float = 5.0, **kwargs: Any):
        """Create a new dummy acquisition."""
        Module.__init__(self, **kwargs)

        # store
        self._wait_secs = wait_secs
        self._is_running = False

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        return self._is_running

    @timeout(120)
    async def acquire_target(self, **kwargs: Any) -> Dict[str, Any]:
        """Acquire target at given coordinates.

        If no RA/Dec are given, start from current position. Might not work for some implementations that require
        coordinates.

        Returns:
            A dictionary with entries for datetime, ra, dec, alt, az, and either off_ra, off_dec or off_alt, off_az.

        Raises:
            ValueError: If target could not be acquired.
        """

        try:
            self._is_running = True
            return await self._acquire()
        finally:
            self._is_running = False

    async def _acquire(self) -> Dict[str, Any]:
        """Actually acquire target."""
        log.info("Acquiring target.")
        await asyncio.sleep(self._wait_secs)
        log.info("Finished.")
        return {}


__all__ = ["DummyAcquisition"]
