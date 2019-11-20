import logging
import threading

from pyobs.interfaces import ICamera, IMotion, ICameraBinning, ICameraWindow
from pyobs.utils.threads import Future
from pyobs.utils.threads.checkabort import check_abort
from .base import LcoBaseConfig


log = logging.getLogger(__name__)


class LcoSkyFlatsConfig(LcoBaseConfig):
    def __init__(self, *args, **kwargs):
        LcoBaseConfig.__init__(self, *args, **kwargs)

    def can_run(self) -> bool:
        """Whether this config can currently run."""

        # we need an open roof and a working telescope
        if self.roof.get_motion_status().wait() not in [IMotion.Status.POSITIONED, IMotion.Status.TRACKING] or \
                self.telescope.get_motion_status().wait() != IMotion.Status.IDLE:
            return False

        # seems alright
        return True

    def __call__(self, abort_event: threading.Event) -> int:
        """Run configuration.

        Args:
            abort_event: Event to abort run.

        Returns:
            Total exposure time in ms.
        """
        raise NotImplementedError


__all__ = ['LcoSkyFlatsConfig']
