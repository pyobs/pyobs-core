from .IMotion import IMotion


class IRoof(IMotion):
    """Base interface for all observatory enclosures."""
    __module__ = 'pyobs.interfaces'
    pass


__all__ = ['IRoof']
