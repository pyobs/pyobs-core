from .IAltAz import IAltAz
from .IRaDec import IRaDec
from .IMotion import IMotion


class ITelescope(IMotion, IAltAz, IRaDec):
    """Generic interface for an astronomical telescope."""
    pass


__all__ = ['ITelescope']
