from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface


class IGain(Interface, metaclass=ABCMeta):
    """The camera supports setting of gain, to be used together with :class:`~pyobs.interfaces.ICamera`."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def set_gain(self, gain: float, **kwargs: Any) -> None:
        """Set the camera gain.

        Args:
            gain: New camera gain.

        Raises:
            ValueError: If gain could not be set.
        """
        ...

    @abstractmethod
    async def get_gain(self, **kwargs: Any) -> float:
        """Returns the camera binning.

        Returns:
            Current gain.
        """
        ...


__all__ = ["IGain"]
