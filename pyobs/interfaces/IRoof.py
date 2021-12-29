from abc import ABCMeta

from .IMotion import IMotion


class IRoof(IMotion, metaclass=ABCMeta):
    """The module controls a roof."""
    __module__ = 'pyobs.interfaces'
    pass


__all__ = ['IRoof']
