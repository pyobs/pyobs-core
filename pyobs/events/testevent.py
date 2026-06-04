from typing import Any, TypedDict

from .event import Event

DataType = TypedDict("DataType", {"message": str | None})


class TestEvent(Event):
    """Just a test event."""

    __module__ = "pyobs.events"

    def __init__(self, message: str | None = None, **kwargs: Any):
        Event.__init__(self)
        self.data["message"] = message


__all__ = ["TestEvent"]
