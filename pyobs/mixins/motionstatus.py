import logging

from pyobs import Module
from pyobs.events import MotionStatusChangedEvent
from pyobs.interfaces import IMotion

log = logging.getLogger(__name__)


class MotionStatusMixin:
    """Mixin for IMotion devices for handling status."""
    def __init__(self, motion_status_interfaces: list = None, *args, **kwargs):
        """Initializes the mixin.

        Args:
            interfaces: List of interfaces to handle or None
        """
        self.__motion_status_interfaces = [] if motion_status_interfaces is None else motion_status_interfaces
        self.__motion_status = IMotion.Status.UNKNOWN
        self.__motion_status_single = {i: IMotion.Status.UNKNOWN for i in self.__motion_status_interfaces}

    def open(self):
        # subscribe to events
        self: (Module, MotionStatusMixin)
        if self.comm:
            self.comm.register_event(MotionStatusChangedEvent)

    def _change_motion_status(self, status: IMotion.Status, interface: str = None):
        """Change motion status and send event,

        Args:
            status: New motion status
            interface: Interface to set motion status for
        """
        self: (Module, MotionStatusMixin)

        # did something change?
        changed = False

        # global or individual?
        if interface is None:
            # did status change?
            if self.__motion_status != status:
                # set it
                changed = True
                self.__motion_status = status

                # also set all individual interfaces
                for i in self.__motion_status_interfaces:
                    if self.__motion_status_single[i] != status:
                        changed = True
                        self.__motion_status_single[i] = status

        else:
            # does it exist?
            if interface not in self.__motion_status_interfaces:
                return

            # did status change?
            if self.__motion_status_single[interface] != status:
                # set it
                self.__motion_status_single[interface] = status
                changed = True

                # combine status
                self.__motion_status = self._combine_motion_status()

        # send event
        if changed:
            self.comm.send_event(MotionStatusChangedEvent(status=self.__motion_status,
                                                          interfaces=self.__motion_status_single))

    def _combine_motion_status(self):
        """Method for combining motion statuses for individual interfaces into the global one. Can be overriden."""

        # none?
        if len(self.__motion_status_interfaces) == 0:
            return

        # if any interface is of state ERROR, UNKNOWN, INITIALIZING, PARKING, SLEWING
        # we use that as global status (in that order)
        for status in [IMotion.Status.ERROR, IMotion.Status.UNKNOWN,
                       IMotion.Status.INITIALIZING, IMotion.Status.PARKING, IMotion.Status.SLEWING]:
            if status in self.__motion_status_single.values():
                return status

        # otherwise just take status of first interface
        return self.__motion_status_single[self.__motion_status_interfaces[0]]

    def get_motion_status(self, interface: str = None, *args, **kwargs) -> IMotion.Status:
        """Returns current motion status.

        Args:
            interface: Name of interface to get status for, or None.

        Returns:
            A string from the Status enumerator.

        Raises:
            KeyError: If interface is not known.
        """

        # global or individual?
        if interface is None:
            return self.__motion_status

        else:
            # does it exist?
            if interface in self.__motion_status_single:
                return self.__motion_status_single[interface]
            else:
                raise KeyError


__all__ = ['MotionStatusMixin']
