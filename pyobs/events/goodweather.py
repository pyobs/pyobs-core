from typing import Any, TypedDict

from pyobs.utils.time import Time
from pyobs.events.event import Event

DataType = TypedDict("DataType", {"eta": str | None})


class GoodWeatherEvent(Event):
    """Event to be sent on good weather."""

    __module__ = "pyobs.events"

    def __init__(self, eta: Time | None = None, **kwargs: Any):
        """Initializes a new good weather event.

        Args:
            eta: Predicted ETA for when the telescope will be fully operational
        """
        Event.__init__(self)
        self.data: DataType = {"eta": eta.isot if eta is not None else None}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Event:
        # get eta
        eta: Time | None = None
        if "eta" in d and isinstance(d["eta"], str):
            eta = Time(d["eta"])

        # return object
        return GoodWeatherEvent(eta=eta)

    @property
    def eta(self) -> Time | None:
        return Time(self.data["eta"]) if self.data["eta"] is not None else None


__all__ = ["GoodWeatherEvent"]
