from typing import Any, TypedDict

from .event import Event

DataType = TypedDict("DataType", {"focus": float, "error": float | None, "filter_name": str | None})


class FocusFoundEvent(Event):
    """Event to be sent when a new best focus has been found, e.g. after a focus series."""

    __module__ = "pyobs.events"

    def __init__(self, focus: float, error: float | None = None, filter_name: str | None = None, **kwargs: Any):
        Event.__init__(self)
        self.data: DataType = {"focus": focus, "error": error, "filter_name": filter_name}

    @property
    def focus(self) -> float:
        return self.data["focus"]

    @property
    def error(self) -> float | None:
        return self.data["error"]

    @property
    def filter_name(self) -> str | None:
        return self.data["filter_name"]


__all__ = ["FocusFoundEvent"]
