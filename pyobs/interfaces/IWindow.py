from abc import ABCMeta, abstractmethod
from typing import Tuple, Any

from .interface import Interface


class IWindow(Interface, metaclass=ABCMeta):
    """The camera supports windows, to be used together with :class:`~pyobs.interfaces.ICamera`."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def get_full_frame(self, **kwargs: Any) -> Tuple[int, int, int, int]:
        """Returns full size of CCD.

        Returns:
            Tuple with left, top, width, and height set.
        """
        ...

    @abstractmethod
    async def set_window(self, left: int, top: int, width: int, height: int, **kwargs: Any) -> None:
        """Set the camera window.

        Args:
            left: X offset of window.
            top: Y offset of window.
            width: Width of window.
            height: Height of window.

        Raises:
            ValueError: If window could not be set.
        """
        ...

    @abstractmethod
    async def get_window(self, **kwargs: Any) -> Tuple[int, int, int, int]:
        """Returns the camera window.

        Returns:
            Tuple with left, top, width, and height set.
        """
        ...


__all__ = ["IWindow"]
