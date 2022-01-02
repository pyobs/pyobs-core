from typing_extensions import TypedDict
from typing import Any

from pyobs.events import Event


class OffsetsEvent(Event):
    """Event to be sent when an offset is to be moved."""

    __module__ = "pyobs.events"
    pass


DataTypeRaDec = TypedDict("DataTypeRaDec", {"ra": float, "dec": float})


class OffsetsRaDecEvent(OffsetsEvent):
    """Event to be sent when an RA/Dec offset is to be moved."""

    __module__ = "pyobs.events"

    def __init__(self, ra: float, dec: float, **kwargs: Any):
        OffsetsEvent.__init__(self)
        self.data: DataTypeRaDec = {"ra": ra, "dec": dec}

    @property
    def ra(self) -> float:
        return self.data["ra"]

    @property
    def dec(self) -> float:
        return self.data["dec"]


DataTypeAltAz = TypedDict("DataTypeAltAz", {"alt": float, "az": float})


class OffsetsAltAzEvent(OffsetsEvent):
    """Event to be sent when an RA/Dec offset is to be moved."""

    __module__ = "pyobs.events"

    def __init__(self, alt: float, az: float, **kwargs: Any):
        OffsetsEvent.__init__(self)
        self.data: DataTypeAltAz = {"alt": alt, "az": az}

    @property
    def alt(self) -> float:
        return self.data["alt"]

    @property
    def az(self) -> float:
        return self.data["az"]


__all__ = ["OffsetsEvent", "OffsetsRaDecEvent", "OffsetsAltAzEvent"]
