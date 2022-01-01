from typing import Optional, Any, Dict
from typing_extensions import TypedDict

from pyobs.events.event import Event
from pyobs.utils.enums import ExposureStatus


DataType = TypedDict("DataType", {"last": Optional[str], "current": str})


class ExposureStatusChangedEvent(Event):
    """Event to be sent, when the exposure status of a device changes."""

    __module__ = "pyobs.events"

    def __init__(self, current: ExposureStatus, last: Optional[ExposureStatus] = None, **kwargs: Any):
        Event.__init__(self)
        self.data: DataType = {
            "last": last.value if last is not None else None,
            "current": current.value,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Event:
        # get current
        if "current" not in d or not isinstance(d["current"], str):
            raise ValueError("Invalid type for current.")
        current: ExposureStatus = ExposureStatus(d["current"])

        # get last
        last: Optional[ExposureStatus] = None
        if "last" in d and isinstance(d["last"], str):
            last = ExposureStatus(d["last"])

        # return object
        return ExposureStatusChangedEvent(current=current, last=last)

    @property
    def last(self) -> Optional[ExposureStatus]:
        return ExposureStatus(self.data["last"]) if self.data["last"] is not None else None

    @property
    def current(self) -> ExposureStatus:
        return ExposureStatus(self.data["current"])


__all__ = ["ExposureStatusChangedEvent"]
