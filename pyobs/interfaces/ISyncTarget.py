from .interface import *


class ISyncTarget(Interface):
    """The module can synchronize a target, e.g. via a telescope control software behinde an
    :class:`~pyobs.interfaces.ITelescope`."""
    __module__ = 'pyobs.interfaces'

    def sync_target(self, *args, **kwargs):
        """Synchronize device on current target."""
        raise NotImplementedError


__all__ = ['ISyncTarget']
