from abc import ABCMeta

from .IMotion import IMotion


class ITelescope(IMotion, metaclass=ABCMeta):
    """The module controls a telescope."""

    __module__ = "pyobs.interfaces"
    pass


__all__ = ["ITelescope"]
