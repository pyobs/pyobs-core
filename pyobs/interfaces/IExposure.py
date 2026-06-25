from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field

from pyobs.utils.enums import ExposureStatus

from ..utils.time import Time
from .interface import Interface


class IExposure(Interface, metaclass=ABCMeta):
    """The module controls a camera."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        status: ExposureStatus
        progress: float
        time: Time = field(default_factory=Time.now)


__all__ = ["IExposure"]
