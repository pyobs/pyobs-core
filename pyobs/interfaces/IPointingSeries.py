from abc import ABCMeta
from typing import Any

from .interface import Interface


class IPointingSeries(Interface, metaclass=ABCMeta):
    """The module provides the interface for a device that initializes and finalizes a pointing series and adds points
    to it."""
    __module__ = 'pyobs.interfaces'

    async def start_pointing_series(self, **kwargs: Any) -> str:
        """Start a new pointing series.

        Returns:
            A unique ID or filename, by which the series can be identified.
        """
        raise NotImplementedError

    async def stop_pointing_series(self, **kwargs: Any) -> None:
        """Stop a pointing series."""
        raise NotImplementedError

    async def add_pointing_measure(self, **kwargs: Any) -> None:
        """Add a new measurement to the pointing series."""
        raise NotImplementedError


__all__ = ['IPointingSeries']
