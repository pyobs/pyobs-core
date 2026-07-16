from abc import ABCMeta

from .IData import IData


class ISpectrograph(IData, metaclass=ABCMeta):
    """The module controls a camera."""

    __module__ = "pyobs.interfaces"
    pass


__all__ = ["ISpectrograph"]
