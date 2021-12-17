from abc import ABCMeta
from typing import Any

from .interface import Interface


class ISyncTarget(Interface, metaclass=ABCMeta):
    """The module can synchronize a target, e.g. via a telescope control software behinde an
    :class:`~pyobs.interfaces.ITelescope`."""
    __module__ = 'pyobs.interfaces'

    async def sync_target(self, **kwargs: Any) -> None:
        """Synchronize device on current target."""
        raise NotImplementedError


__all__ = ['ISyncTarget']
