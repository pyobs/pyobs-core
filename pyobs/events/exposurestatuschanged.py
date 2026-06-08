from __future__ import annotations

from typing import Any, TypedDict

from pyobs.events.event import Event
from pyobs.utils.enums import ExposureStatus


class DataType(TypedDict):
    last: str | None
    current: str


class ExposureStatusChangedEvent(Event):
    """Event to be sent, when the exposure status of a device changes."""

    __module__ = "pyobs.events"

    def __init__(self, current: ExposureStatus, last: ExposureStatus | None = None, **kwargs: Any):
        Event.__init__(self)
        self.data: DataType = {
            "last": last if last is not None else None,
            "current": current,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Event:
        # get current
        if "current" not in d or not isinstance(d["current"], str):
            raise ValueError("Invalid type for current.")
        current: ExposureStatus = ExposureStatus(d["current"])

        # get last
        last: ExposureStatus | None = None
        if "last" in d and isinstance(d["last"], str):
            last = ExposureStatus(d["last"])

        # return object
        return ExposureStatusChangedEvent(current=current, last=last)

    @property
    def last(self) -> ExposureStatus | None:
        return ExposureStatus(self.data["last"]) if self.data["last"] is not None else None

    @property
    def current(self) -> ExposureStatus:
        return ExposureStatus(self.data["current"])


__all__ = ["ExposureStatusChangedEvent"]
