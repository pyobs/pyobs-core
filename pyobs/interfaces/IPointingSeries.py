from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface


class IPointingSeries(Interface, metaclass=ABCMeta):
    """The module provides the interface for a device that initializes and finalizes a pointing series and adds points
    to it."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def start_pointing_series(self, **kwargs: Any) -> str:
        """Start a new pointing series.

        Returns:
            A unique ID or filename, by which the series can be identified.
        """
        ...

    @abstractmethod
    async def stop_pointing_series(self, **kwargs: Any) -> None:
        """Stop a pointing series."""
        ...

    @abstractmethod
    async def add_pointing_measure(self, **kwargs: Any) -> None:
        """Add a new measurement to the pointing series."""
        ...


__all__ = ["IPointingSeries"]
