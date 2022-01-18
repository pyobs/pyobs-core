from abc import ABCMeta, abstractmethod
from typing import List, Any

from .IMotion import IMotion


class IFilters(IMotion, metaclass=ABCMeta):
    """The module can change filters in a device."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def list_filters(self, **kwargs: Any) -> List[str]:
        """List available filters.

        Returns:
            List of available filters.
        """
        ...

    @abstractmethod
    async def set_filter(self, filter_name: str, **kwargs: Any) -> None:
        """Set the current filter.

        Args:
            filter_name: Name of filter to set.

        Raises:
            ValueError: If an invalid filter was given.
            MoveError: If filter wheel cannot be moved.
        """
        ...

    @abstractmethod
    async def get_filter(self, **kwargs: Any) -> str:
        """Get currently set filter.

        Returns:
            Name of currently set filter.
        """
        ...


__all__ = ["IFilters"]
