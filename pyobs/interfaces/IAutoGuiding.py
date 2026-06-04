from abc import ABCMeta

from .IExposureTime import IExposureTime
from .IStartStop import IStartStop


class IAutoGuiding(IStartStop, IExposureTime, metaclass=ABCMeta):
    """The module can perform auto-guiding."""

    __module__ = "pyobs.interfaces"


__all__ = ["IAutoGuiding"]
