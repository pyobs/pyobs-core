from abc import ABCMeta

from .IExposure import IExposure
from .IAbortable import IAbortable
from .IData import IData


class ICamera(IAbortable, IData, IExposure, metaclass=ABCMeta):
    """The module controls a camera."""

    __module__ = "pyobs.interfaces"
    pass


__all__ = ["ICamera"]
