from abc import ABCMeta


class Interface(metaclass=ABCMeta):
    """Base class for all interfaces in pyobs."""

    version: int = 1

    __module__ = "pyobs.interfaces"
    pass


__all__ = ["Interface"]
