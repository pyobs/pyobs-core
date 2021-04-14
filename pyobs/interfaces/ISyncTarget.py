from .interface import *


class ISyncTarget(Interface):
    """Interface for all devices that can be synchronized on a target."""
    __module__ = 'pyobs.interfaces'

    def sync_target(self, *args, **kwargs):
        """Synchronize device on current target."""
        raise NotImplementedError


__all__ = ['ISyncTarget']
