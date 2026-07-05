from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field
from typing import Annotated

from ..utils.enums import OffsetFrame, Unit
from ..utils.time import Time
from .IExposureTime import IExposureTime
from .IStartStop import IStartStop


@dataclass
class GuidingState:  # live open/closed-loop status, separate from the per-session FITS-header RMS stats
    loop_closed: bool = False
    # the correction applied for the last processed image, in the mount's native frame
    offset_frame: OffsetFrame | None = None
    offset_lon: Annotated[float, Unit.DEGREES] | None = None
    offset_lat: Annotated[float, Unit.DEGREES] | None = None
    time: Time = field(default_factory=Time.now)


class IAutoGuiding(IStartStop, IExposureTime, metaclass=ABCMeta):
    """The module can perform auto-guiding."""

    __module__ = "pyobs.interfaces"

    state = GuidingState


__all__ = ["IAutoGuiding", "GuidingState"]
