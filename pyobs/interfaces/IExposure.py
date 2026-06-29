from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field
from typing import Annotated

from pyobs.utils.enums import ExposureStatus, Unit

from ..utils.time import Time
from .interface import Interface


class IExposure(Interface, metaclass=ABCMeta):
    """The module controls a camera."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        status: ExposureStatus
        progress: Annotated[float, Unit.PERCENT]
        exposure_time_left: Annotated[float, Unit.SECONDS] = 0.0
        time: Time = field(default_factory=Time.now)


__all__ = ["IExposure"]
