from .IRoof import IRoof
from .IAltAz import IAltAz


class IDome(IRoof, IAltAz):
    """The module controls a dome, i.e. a :class:`~pyobs.interfaces.IRoof` with a rotating roof."""
    __module__ = 'pyobs.interfaces'
    pass


__all__ = ['IDome']
