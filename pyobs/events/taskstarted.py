from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

from pyobs.events.event import Event

if TYPE_CHECKING:
    from pyobs.utils.time import Time


class DataType(TypedDict):
    name: str
    id: Any
    eta: str | None
    obsnum: str | None


class TaskStartedEvent(Event):
    """Event to be sent when a task has started."""

    __module__ = "pyobs.events"

    def __init__(self, name: str, id: Any, eta: Time | None = None, obsnum: str | None = None, **kwargs: Any):
        """Initializes a new task started event.

        Args:
            name: Name of task that just started
            id: Unique identifier for task
            eta: Predicted ETA for when the task will finish
            obsnum: Per-night observation number assigned to this run, e.g. "20260810-001"
        """
        Event.__init__(self)
        self.data: DataType = {"name": name, "id": id, "eta": None if eta is None else eta.isot, "obsnum": obsnum}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Event:
        from pyobs.utils.time import Time

        # get name
        if "name" not in d or not isinstance(d["name"], str):
            raise ValueError("Invalid type for name.")
        name: str = d["name"]

        # get id
        if "id" not in d:
            raise ValueError("Invalid type for id.")
        id: Any = d["id"]

        # get eta
        eta: Time | None = None
        if "eta" in d and isinstance(d["eta"], str):
            eta = Time(d["eta"])

        # get obsnum
        obsnum: str | None = d["obsnum"] if isinstance(d.get("obsnum"), str) else None

        # return object
        return TaskStartedEvent(name=name, id=id, eta=eta, obsnum=obsnum)

    @property
    def name(self) -> str:
        return self.data["name"]

    @property
    def id(self) -> Any:
        return self.data["id"]

    @property
    def eta(self) -> Time | None:
        from pyobs.utils.time import Time

        return Time(self.data["eta"]) if self.data["eta"] is not None else None

    @property
    def obsnum(self) -> str | None:
        return self.data["obsnum"]


__all__ = ["TaskStartedEvent"]
