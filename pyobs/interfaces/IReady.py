from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface


class IReady(Interface, metaclass=ABCMeta):
    """The module can be in a "not ready" state for science and need to be initialized in some way."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def is_ready(self, **kwargs: Any) -> bool:
        """Returns the device is "ready", whatever that means for the specific device.

        Returns:
            Whether device is ready
        """
        ...


__all__ = ["IReady"]
