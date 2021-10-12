import logging
import time

from pyobs.interfaces import IAcquisition
from pyobs.modules import Module
from pyobs.modules import timeout

log = logging.getLogger(__name__)


class DummyAcquisition(Module, IAcquisition):
    """Dummy class for telescope acquisition."""
    __module__ = 'pyobs.modules.acquisition'

    def __init__(self, *args, **kwargs):
        """Create a new dummy acquisition."""
        Module.__init__(self, *args, **kwargs)

        # store
        self._is_running = False

    def is_running(self, *args, **kwargs) -> bool:
        """Whether a service is running."""
        return self._is_running

    @timeout(120)
    def acquire_target(self, exposure_time: float, *args, **kwargs) -> dict:
        """Acquire target at given coordinates.

        If no RA/Dec are given, start from current position. Might not work for some implementations that require
        coordinates.

        Args:
            exposure_time: Exposure time for acquisition in secs.

        Returns:
            A dictionary with entries for datetime, ra, dec, alt, az, and either off_ra, off_dec or off_alt, off_az.

        Raises:
            ValueError: If target could not be acquired.
        """

        try:
            self._is_running = True
            return self._acquire(exposure_time)
        finally:
            self._is_running = False

    def _acquire(self, exposure_time: float) -> dict:
        """Actually acquire target."""
        time.sleep(5)
        return {}


__all__ = ['DummyAcquisition']
