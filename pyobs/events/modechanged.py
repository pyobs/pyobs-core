from typing import Optional, Any
from typing_extensions import TypedDict

from .event import Event


DataType = TypedDict("DataType", {"group": str, "current": str})


class ModeChangedEvent(Event):
    """Event to be sent when a mode has been changed."""

    __module__ = "pyobs.events"

    def __init__(self, group: str, current: str, **kwargs: Any):
        Event.__init__(self)
        self.data: DataType = {"group": group, "current": current}

    @property
    def mode(self) -> str:
        return self.data["current"]

    @property
    def group(self) -> str:
        return self.data["group"]


__all__ = ["ModeChangedEvent"]
