import logging
import threading

from pyobs.events import RoofOpenedEvent, RoofClosingEvent
from pyobs.interfaces import IRoof, IMotion
from pyobs.modules import timeout
from pyobs.modules.roof import BaseRoof
from pyobs.utils.threads import LockWithAbort

log = logging.getLogger(__name__)


class DummyRoof(BaseRoof, IRoof):
    """A dummy camera for testing."""

    def __init__(self, *args, **kwargs):
        """Creates a new dummy root."""
        BaseRoof.__init__(self, *args, **kwargs)

        # dummy state
        self.open_percentage = 0

        # allow to abort motion
        self._lock_motion = threading.Lock()
        self._abort_motion = threading.Event()

        # register event
        self.comm.register_event(RoofOpenedEvent)
        self.comm.register_event(RoofClosingEvent)

    @timeout(15000)
    def open_roof(self, *args, **kwargs):
        """Open the roof."""

        # already open?
        if self.open_percentage != 100:
            # acquire lock
            with LockWithAbort(self._lock_motion, self._abort_motion):
                # change status
                self._change_motion_status(IMotion.Status.INITIALIZING)

                # open roof
                while self.open_percentage < 100:
                    # open more
                    self.open_percentage += 1

                    # abort?
                    if self._abort_motion.is_set():
                        self._change_motion_status(IMotion.Status.IDLE)
                        return

                    # wait a little
                    self.closing.wait(0.1)

                # open fully
                self.open_percentage = 100

                # change status
                self._change_motion_status(IMotion.Status.IDLE)

                # send event
                self.comm.send_event(RoofOpenedEvent())

    @timeout(15000)
    def close_roof(self, *args, **kwargs):
        """Close the roof."""

        # already closed?
        if self.open_percentage != 0:
            # acquire lock
            with LockWithAbort(self._lock_motion, self._abort_motion):
                # change status
                self._change_motion_status(IMotion.Status.PARKING)

                # send event
                self.comm.send_event(RoofClosingEvent())

                # close roof
                while self.open_percentage > 0:
                    # close more
                    self.open_percentage -= 1

                    # abort?
                    if self._abort_motion.is_set():
                        self._change_motion_status(IMotion.Status.IDLE)
                        return

                    # wait a little
                    self.closing.wait(0.1)

                # change status
                self._change_motion_status(IMotion.Status.PARKED)

    def get_percent_open(self) -> float:
        """Get the percentage the roof is open."""
        return self.open_percentage

    def stop_motion(self, device: str = None):
        """Stop the motion.

        Args:
            device: Name of device to stop, or None for all.
        """

        # change status
        self._change_motion_status(IMotion.Status.ABORTING)

        # abort
        # acquire lock
        with LockWithAbort(self._lock_motion, self._abort_motion):
            # change status
            self._change_motion_status(IMotion.Status.IDLE)


__all__ = ['DummyRoof']
