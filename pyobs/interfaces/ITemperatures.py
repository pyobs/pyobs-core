from abc import ABCMeta
from typing import Any, Dict

from .interface import Interface


class ITemperatures(Interface, metaclass=ABCMeta):
    """The module can return temperatures measured on some device."""
    __module__ = 'pyobs.interfaces'

    async def get_temperatures(self, **kwargs: Any) -> Dict[str, float]:
        """Returns all temperatures measured by this module.

        Returns:
            Dict containing temperatures.
        """
        raise NotImplementedError


__all__ = ['ITemperatures']
