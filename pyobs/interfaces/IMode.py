from abc import ABCMeta, abstractmethod
from typing import List, Any

from .interface import Interface


class IMode(Interface, metaclass=ABCMeta):
    """The module can change modes in a device."""

    __module__ = "pyobs.interfaces"

    async def list_mode_groups(self) -> List[str]:
        """List names of mode groups that can be set. The index is used as the `group` parameter in the individual
        methods.

        Returns:
            List of names of mode groups.
        """
        return []

    @abstractmethod
    async def list_modes(self, group: int = 0, **kwargs: Any) -> List[str]:
        """List available modes.

        Args:
            group: Group number

        Returns:
            List of available modes.
        """
        ...

    @abstractmethod
    async def set_mode(self, mode: str, group: int = 0, **kwargs: Any) -> None:
        """Set the current mode.

        Args:
            mode: Name of mode to set.
            group: Group number

        Raises:
            ValueError: If an invalid mode was given.
            MoveError: If mode selector cannot be moved.
        """
        ...

    @abstractmethod
    async def get_mode(self, group: int = 0, **kwargs: Any) -> str:
        """Get currently set mode.

        Args:
            group: Group number

        Returns:
            Name of currently set mode.
        """
        ...


__all__ = ["IMode"]
