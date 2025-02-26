from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface


class IMultiFiber(Interface, metaclass=ABCMeta):
    """An interface for multi-fiber setups that helps to set/get a fiber and retrieve position and size of the
    current fiber on the acquisition/guiding image."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        ...

    async def get_fiber_count(self, **kwargs: Any) -> int:
        """Returns the number of available fibers in the setup.

        Returns:
            Number of fibers.
        """
        ...

    async def list_fiber_names(self, **kwargs: Any) -> list[str]:
        """Returns the names of all available fibers.

        Returns:
            List of fiber names.
        """
        ...

    async def get_fiber(self, **kwargs: Any) -> str:
        """Returns the name of the currently active fiber.

        Returns:
            Name of currently active fiber.
        """
        ...

    async def set_fiber(self, fiber: str, **kwargs: Any) -> None:
        """Sets the currently active filter. Must be in list returned by @list_fiber_names.

        Args:
            fiber: Name of fiber to set.
        """
        ...

    async def get_pixel_position(self, **kwargs: Any) -> tuple[float, float]:
        """Get pixel position of currently active fiber on acquisition/guiding image.

        Returns:
            x/y pixel position of fiber on image.
        """
        ...

    async def get_radius(self, **kwargs: Any) -> float:
        """Get radius of currently active fiber on acquisition/guiding image.

        Returns:
            radius of fiber on image.
        """
        ...


__all__ = ["IMultiFiber"]
