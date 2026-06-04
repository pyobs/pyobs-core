from typing import Any, TypedDict

from pyobs.events.event import Event
from pyobs.utils.enums import MotionStatus

DataType = TypedDict("DataType", {"status": str, "interfaces": dict[str, str]})


class MotionStatusChangedEvent(Event):
    """Event to be sent when the motion status of a device has changed."""

    __module__ = "pyobs.events"

    def __init__(self, status: MotionStatus, interfaces: dict[str, MotionStatus] | None = None, **kwargs: Any):
        Event.__init__(self)
        self.data: DataType = {
            "status": status.value,
            "interfaces": {k: v.value for k, v in interfaces.items()} if interfaces is not None else {},
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Event:
        # get status
        if "status" not in d or not isinstance(d["status"], str):
            raise ValueError("Invalid type for status.")
        status: MotionStatus = MotionStatus(d["status"])

        # get interfaces
        interfaces: dict[str, MotionStatus] | None = {}
        if "interfaces" in d and isinstance(d["interfaces"], dict):
            interfaces = {k: MotionStatus(v) for k, v in d["interfaces"].items()}

        # return object
        return MotionStatusChangedEvent(status, interfaces)

    @property
    def status(self) -> MotionStatus:
        return MotionStatus(self.data["status"])

    @property
    def interfaces(self) -> dict[str, MotionStatus]:
        return {k: MotionStatus(v) for k, v in self.data["interfaces"].items()}


__all__ = ["MotionStatusChangedEvent"]
