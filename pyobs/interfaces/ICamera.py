from abc import ABCMeta

from .IData import IData
from .IExposure import IExposure


class ICamera(IData, IExposure, metaclass=ABCMeta):
    """The module controls a camera."""

    __module__ = "pyobs.interfaces"
    pass


__all__ = ["ICamera"]
