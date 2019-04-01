import logging

from pyobs import PyObsModule
from pyobs.events import RoofOpenedEvent, RoofClosingEvent
from pyobs.interfaces import IRoof, IMotion

log = logging.getLogger(__name__)


class DummyRoof(PyObsModule, IRoof):
    """A dummy camera for testing."""

    def __init__(self, *args, **kwargs):
        """Creates a new dummy root."""
        PyObsModule.__init__(self, *args, **kwargs)

        # dummy state
        self.open_percentage = 0
        self.motion_state = IMotion.Status.PARKED

        # register event
        self.comm.register_event(RoofOpenedEvent)
        self.comm.register_event(RoofClosingEvent)

    def open_roof(self, *args, **kwargs):
        """Open the roof."""

        # already open?
        if self.open_percentage != 100:
            # open roof
            while self.open_percentage < 100:
                self.open_percentage += 1
                self.closing.wait(0.1)
            self.open_percentage = 100

            # send event
            self.comm.send_event(RoofOpenedEvent())

    def close_roof(self, *args, **kwargs):
        """Close the roof."""

        # already closed?
        if self.open_percentage != 0:
            # send event
            self.comm.send_event(RoofClosingEvent())

            # close roof
            while self.open_percentage > 0:
                self.open_percentage -= 1
                self.closing.wait(0.1)

    def halt_roof(self, *args, **kwargs):
        pass

    def get_motion_status(self, device: str = None) -> IMotion.Status:
        """Returns current motion status.

        Args:
            device: Name of device to get status for, or None.

        Returns:
            Roof status.
        """
        pass


__all__ = ['DummyRoof']
