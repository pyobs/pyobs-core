from abc import ABCMeta

from .IPointingAltAz import IPointingAltAz
from .IRoof import IRoof


class IDome(IRoof, IPointingAltAz, metaclass=ABCMeta):
    """The module controls a dome, i.e. a :class:`~pyobs.interfaces.IRoof` with a rotating roof."""

    __module__ = "pyobs.interfaces"
    pass


__all__ = ["IDome"]
