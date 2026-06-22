from abc import ABCMeta
from typing import ClassVar


class Interface(metaclass=ABCMeta):
    """Base class for all interfaces in pyobs."""

    version: int = 1
    state: ClassVar[type | None] = None

    __module__ = "pyobs.interfaces"
    pass


__all__ = ["Interface"]
