from .IPointingAltAz import IPointingAltAz
from .IPointingRaDec import IPointingRaDec
from .IMotion import IMotion


class ITelescope(IMotion, IPointingAltAz, IPointingRaDec):
    """The module controls a telescope."""
    __module__ = 'pyobs.interfaces'
    pass


__all__ = ['ITelescope']
