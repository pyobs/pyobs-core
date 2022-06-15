from abc import ABCMeta

from .IStartStop import IStartStop
from .IExposureTime import IExposureTime


class IAutoGuiding(IStartStop, IExposureTime, metaclass=ABCMeta):
    """The module can perform auto-guiding."""

    __module__ = "pyobs.interfaces"


__all__ = ["IAutoGuiding"]
