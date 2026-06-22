from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Annotated, Any

from ..utils.enums import Unit
from .interface import Interface


class ITemperatures(Interface, metaclass=ABCMeta):
    """The module can return temperatures measured on some device."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def get_temperatures(self, **kwargs: Any) -> dict[str, Annotated[float, Unit.CELSIUS]]:
        """Returns all temperatures measured by this module.

        Returns:
            Dict containing temperatures.
        """
        ...


__all__ = ["ITemperatures"]
