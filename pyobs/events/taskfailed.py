from typing import Any, TypedDict

from pyobs.events.event import Event


class DataType(TypedDict):
    name: str
    id: Any
    obsnum: str | None


class TaskFailedEvent(Event):
    """Event to be sent when a task has failed."""

    __module__ = "pyobs.events"

    def __init__(self, name: str, id: Any, obsnum: str | None = None, **kwargs: Any):
        """Initializes a new task failed event.

        Args:
            name: Name of task that just failed
            id: Unique identifier for task
            obsnum: Per-night observation number of the run that just failed, e.g. "20260810-001"
        """
        Event.__init__(self)
        self.data: DataType = {"name": name, "id": id, "obsnum": obsnum}

    @property
    def name(self) -> str:
        return self.data["name"]

    @property
    def id(self) -> Any:
        return self.data["id"]

    @property
    def obsnum(self) -> str | None:
        return self.data["obsnum"]


__all__ = ["TaskFailedEvent"]
