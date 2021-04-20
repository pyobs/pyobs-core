from .IAltAz import IAltAz
from .IRaDec import IRaDec
from .IMotion import IMotion


class ITelescope(IMotion, IAltAz, IRaDec):
    """The module controls a telescope."""
    __module__ = 'pyobs.interfaces'
    pass


__all__ = ['ITelescope']
