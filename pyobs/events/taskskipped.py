from typing import Any, TypedDict

from pyobs.events.event import Event


class DataType(TypedDict):
    name: str
    id: Any
    reason: str


class TaskSkippedEvent(Event):
    """Event to be sent when a scheduled task is skipped without running."""

    __module__ = "pyobs.events"

    def __init__(self, name: str, id: Any, reason: str, **kwargs: Any):
        """Initializes a new task skipped event.

        Args:
            name: Name of task that was skipped
            id: Unique identifier for task
            reason: Human-readable reason why the task was skipped
        """
        Event.__init__(self)
        self.data: DataType = {"name": name, "id": id, "reason": reason}

    @property
    def name(self) -> str:
        return self.data["name"]

    @property
    def id(self) -> Any:
        return self.data["id"]

    @property
    def reason(self) -> str:
        return self.data["reason"]


__all__ = ["TaskSkippedEvent"]
