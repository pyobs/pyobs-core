from abc import ABCMeta, abstractmethod
from typing import Any, Dict

from .interface import Interface


class ITemperatures(Interface, metaclass=ABCMeta):
    """The module can return temperatures measured on some device."""
    __module__ = 'pyobs.interfaces'

    @abstractmethod
    async def get_temperatures(self, **kwargs: Any) -> Dict[str, float]:
        """Returns all temperatures measured by this module.

        Returns:
            Dict containing temperatures.
        """
        ...


__all__ = ['ITemperatures']
