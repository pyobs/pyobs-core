from typing_extensions import TypedDict
from typing import Any

from pyobs.events import Event


class MoveEvent(Event):
    """Event to be sent when moving to a new target."""

    __module__ = "pyobs.events"
    pass


DataTypeRaDec = TypedDict("DataTypeRaDec", {"ra": float, "dec": float})


class MoveRaDecEvent(MoveEvent):
    """Event to be sent when moving to RA/Dec."""

    __module__ = "pyobs.events"

    def __init__(self, ra: float, dec: float, **kwargs: Any):
        MoveEvent.__init__(self)
        self.data: DataTypeRaDec = {"ra": ra, "dec": dec}

    @property
    def ra(self) -> float:
        return self.data["ra"]

    @property
    def dec(self) -> float:
        return self.data["dec"]


DataTypeAltAz = TypedDict("DataTypeAltAz", {"alt": float, "az": float})


class MoveAltAzEvent(MoveEvent):
    """Event to be sent when moving to Alt/Az."""

    __module__ = "pyobs.events"

    def __init__(self, alt: float, az: float, **kwargs: Any):
        MoveEvent.__init__(self)
        self.data: DataTypeAltAz = {"alt": alt, "az": az}

    @property
    def alt(self) -> float:
        return self.data["alt"]

    @property
    def az(self) -> float:
        return self.data["az"]


__all__ = ["MoveEvent", "MoveRaDecEvent", "MoveAltAzEvent"]
