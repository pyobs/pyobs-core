from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field

from ..utils.time import Time
from .IExposureTime import IExposureTime
from .IStartStop import IStartStop


@dataclass
class GuidingState:  # live open/closed-loop status, separate from the per-session FITS-header RMS stats
    loop_closed: bool = False
    last_offset_x: float | None = None  # pixel offset, axis 1
    last_offset_y: float | None = None  # pixel offset, axis 2
    time: Time = field(default_factory=Time.now)


class IAutoGuiding(IStartStop, IExposureTime, metaclass=ABCMeta):
    """The module can perform auto-guiding."""

    __module__ = "pyobs.interfaces"

    state = GuidingState


__all__ = ["IAutoGuiding", "GuidingState"]
