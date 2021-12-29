from abc import ABCMeta, abstractmethod
from typing import Tuple, List, Any

from .interface import Interface


class IBinning(Interface, metaclass=ABCMeta):
    """The camera supports binning, to be used together with :class:`~pyobs.interfaces.ICamera`."""
    __module__ = 'pyobs.interfaces'

    @abstractmethod
    async def set_binning(self, x: int, y: int, **kwargs: Any) -> None:
        """Set the camera binning.

        Args:
            x: X binning.
            y: Y binning.

        Raises:
            ValueError: If binning could not be set.
        """
        ...

    @abstractmethod
    async def get_binning(self, **kwargs: Any) -> Tuple[int, int]:
        """Returns the camera binning.

        Returns:
            Tuple with x and y.
        """
        ...

    @abstractmethod
    async def list_binnings(self, **kwargs: Any) -> List[Tuple[int, int]]:
        """List available binnings.

        Returns:
            List of available binnings as (x, y) tuples.
        """
        ...


__all__ = ['IBinning']
