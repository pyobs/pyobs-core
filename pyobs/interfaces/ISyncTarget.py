from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface


class ISyncTarget(Interface, metaclass=ABCMeta):
    """The module can synchronize a target, e.g. via a telescope control software behinde an
    :class:`~pyobs.interfaces.ITelescope`."""
    __module__ = 'pyobs.interfaces'

    @abstractmethod
    async def sync_target(self, **kwargs: Any) -> None:
        """Synchronize device on current target."""
        ...


__all__ = ['ISyncTarget']
