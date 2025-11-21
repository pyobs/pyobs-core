from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface


class IPointingSeries(Interface, metaclass=ABCMeta):
    """The module provides the interface for a device that initializes and finalizes a pointing series and adds points
    to it."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def add_pointing_measurement(self, **kwargs: Any) -> None:
        """Add a new measurement to the pointing series."""
        ...


__all__ = ["IPointingSeries"]
