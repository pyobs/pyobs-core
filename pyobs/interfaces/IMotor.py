from abc import ABCMeta

from . import Interface

class IMotor(Interface, metaclass=ABCMeta):
    """The module controls a motor."""

    __module__ = "pyobs.interfaces"
    pass

__all__ = ["IMotor"]