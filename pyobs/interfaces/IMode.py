from abc import ABCMeta, abstractmethod
from typing import List, Any

from .IMotion import IMotion


class IMode(IMotion, metaclass=ABCMeta):
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
    async def set_mode(self, mode_name: str, **kwargs: Any) -> None:
        """Set the current mode.

        Args:
            mode_name: Name of mode to set.

        Raises:
            ValueError: If an invalid mode was given.
            MoveError: If mode wheel cannot be moved.
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
