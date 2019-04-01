import logging

from pyobs.events import MotionStatusChangedEvent
from pyobs.interfaces import IRoof, IMotion
from pyobs import PyObsModule


log = logging.getLogger(__name__)


class BaseRoof(PyObsModule, IRoof):
    """Base class for roofs."""

    def __init__(self, *args, **kwargs):
        """Initialize a new base roof."""
        PyObsModule.__init__(self, *args, **kwargs)

        # status
        self._motion_status = IMotion.Status.PARKED

    def open(self):
        """Open module."""
        PyObsModule.open(self)

        # subscribe to events
        if self.comm:
            self.comm.register_event(MotionStatusChangedEvent)

    def _change_motion_status(self, status: IMotion.Status):
        """Change motion status and send event,

        Args:
            status: New motion status.
        """

        # send event, if it changed
        if self._motion_status != status:
            self.comm.send_event(MotionStatusChangedEvent(self._motion_status, status))

        # set it
        self._motion_status = status

    def get_motion_status(self, device: str = None) -> IMotion.Status:
        """Returns current motion status.

        Args:
            device: Name of device to get status for, or None.

        Returns:
            A string from the Status enumerator.
        """
        return self._motion_status


__all__ = ['BaseRoof']
