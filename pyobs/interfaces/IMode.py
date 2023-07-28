from abc import ABCMeta, abstractmethod
from typing import List, Any

from . import Interface

class IMode(Interface, metaclass=ABCMeta):
    """The module can change modes in a device."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def list_modes(self, **kwargs: Any) -> List[str]:
        """List available modes.

        Returns:
            List of available modes.
        """
        ...

    @abstractmethod
    async def set_mode(self, mode: str, **kwargs: Any) -> None:
        """Set the current mode.

        Args:
            mode: Name of mode to set.

        Raises:
            ValueError: If an invalid mode was given.
            MoveError: If mode selector cannot be moved.
        """
        ...

    @abstractmethod
    async def get_mode(self, **kwargs: Any) -> str:
        """Get currently set mode.

        Returns:
            Name of currently set mode.
        """
        ...


__all__ = ["IMode"]
