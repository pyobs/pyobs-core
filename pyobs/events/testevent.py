from typing import Optional, Any
from typing_extensions import TypedDict

from .event import Event


DataType = TypedDict("DataType", {"message": Optional[str]})


class TestEvent(Event):
    """Just a test event."""

    __module__ = "pyobs.events"

    def __init__(self, message: Optional[str] = None, **kwargs: Any):
        Event.__init__(self)
        self.data["message"] = message


__all__ = ["TestEvent"]
