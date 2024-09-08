import logging
from typing import Any, Optional, List

from pyobs.modules import Module
from pyobs.events import MotionStatusChangedEvent
from pyobs.utils.enums import MotionStatus

log = logging.getLogger(__name__)


class MotionStatusMixin:
    """Mixin for IMotion devices for handling status."""

    __module__ = "pyobs.mixins"

    def __init__(self, motion_status_interfaces: Optional[List[str]] = None, **kwargs: Any):
        """Initializes the mixin.

        Args:
            interfaces: List of interfaces to handle or None
        """
        self.__motion_status_interfaces = [] if motion_status_interfaces is None else motion_status_interfaces
        self.__motion_status = MotionStatus.UNKNOWN
        self.__motion_status_single = {i: MotionStatus.UNKNOWN for i in self.__motion_status_interfaces}

    async def open(self) -> None:
        # subscribe to events
        if isinstance(self, Module) and self.comm:
            await self.comm.register_event(MotionStatusChangedEvent)

    async def _change_motion_status(self, status: MotionStatus, interface: Optional[str] = None) -> None:
        """Change motion status and send event,

        Args:
            status: New motion status
            interface: Interface to set motion status for
        """

        # did something change?
        changed = False

        # global or individual?
        if interface is None:
            # did status change?
            if self.__motion_status != status:
                # log and set it
                changed = True
                self.__motion_status = status
                log.info("Changed motion status to %s.", status)

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
                log.info("Changed motion status for interface %s to %s.", interface, status)

                # combine status
                self.__motion_status = self._combine_motion_status()

        # send event
        if changed:
            this = self

            # log it
            if interface is None:
                log.info("Changed motion status to %s.", status)
            else:
                log.info("Changed motion status of %s to %s.", interface, status)

            # send event
            if not isinstance(self, Module):
                raise ValueError("This is not a module.")
            await self.comm.send_event(
                MotionStatusChangedEvent(status=this.__motion_status, interfaces=this.__motion_status_single)
            )

    def _combine_motion_status(self) -> MotionStatus:
        """Method for combining motion statuses for individual interfaces into the global one. Can be overriden."""

        # none?
        if len(self.__motion_status_interfaces) == 0:
            return MotionStatus.UNKNOWN

        # if any interface is of state ERROR, UNKNOWN, INITIALIZING, PARKING, SLEWING
        # we use that as global status (in that order)
        for status in [
            MotionStatus.ERROR,
            MotionStatus.UNKNOWN,
            MotionStatus.INITIALIZING,
            MotionStatus.PARKING,
            MotionStatus.SLEWING,
        ]:
            if status in self.__motion_status_single.values():
                return status

        # otherwise just take status of first interface
        return self.__motion_status_single[self.__motion_status_interfaces[0]]

    async def get_motion_status(self, device: Optional[str] = None, **kwargs: Any) -> MotionStatus:
        """Returns current motion status.

        Args:
            device: Name of device to get status for, or None.

        Returns:
            A string from the Status enumerator.
        """

        # global or individual?
        if device is None:
            return self.__motion_status

        else:
            # does it exist?
            if device in self.__motion_status_single:
                return self.__motion_status_single[device]
            else:
                raise KeyError


__all__ = ["MotionStatusMixin"]
