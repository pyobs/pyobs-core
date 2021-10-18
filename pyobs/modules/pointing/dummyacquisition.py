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
    def acquire_target(self, *args, **kwargs) -> dict:
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
            return self._acquire()
        finally:
            self._is_running = False

    def _acquire(self) -> dict:
        """Actually acquire target."""
        log.info('Acquiring target.')
        time.sleep(5)
        log.info('Finished.')
        return {}


__all__ = ['DummyAcquisition']
