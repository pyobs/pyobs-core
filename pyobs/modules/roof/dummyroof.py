import logging

from pyobs.events import RoofOpenedEvent, RoofClosingEvent
from pyobs.interfaces import IRoof, IMotion
from pyobs.modules import timeout
from pyobs.modules.roof import BaseRoof

log = logging.getLogger(__name__)


class DummyRoof(BaseRoof, IRoof):
    """A dummy camera for testing."""

    def __init__(self, *args, **kwargs):
        """Creates a new dummy root."""
        BaseRoof.__init__(self, *args, **kwargs)

        # dummy state
        self.open_percentage = 0

        # register event
        self.comm.register_event(RoofOpenedEvent)
        self.comm.register_event(RoofClosingEvent)

    @timeout(15000)
    def open_roof(self, *args, **kwargs):
        """Open the roof."""

        # already open?
        if self.open_percentage != 100:
            # change status
            self._change_motion_status(IMotion.Status.INITIALIZING)

            # open roof
            while self.open_percentage < 100:
                self.open_percentage += 1
                self.closing.wait(0.1)
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
            # change status
            self._change_motion_status(IMotion.Status.PARKING)

            # send event
            self.comm.send_event(RoofClosingEvent())

            # close roof
            while self.open_percentage > 0:
                self.open_percentage -= 1
                self.closing.wait(0.1)

            # change status
            self._change_motion_status(IMotion.Status.PARKED)

    def get_percent_open(self) -> float:
        """Get the percentage the roof is open."""
        return self.open_percentage

    def halt_roof(self, *args, **kwargs):
        pass


__all__ = ['DummyRoof']
