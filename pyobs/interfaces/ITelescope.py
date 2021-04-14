from .IAltAz import IAltAz
from .IRaDec import IRaDec
from .IMotion import IMotion


class ITelescope(IMotion, IAltAz, IRaDec):
    """Generic interface for an astronomical telescope."""
    __module__ = 'pyobs.interfaces'
    pass


__all__ = ['ITelescope']
