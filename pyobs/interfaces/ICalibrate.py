from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface


class ICalibrate(Interface, metaclass=ABCMeta):
    """The module can calibrate a device."""
    __module__ = 'pyobs.interfaces'

    @abstractmethod
    async def calibrate(self, **kwargs: Any) -> None:
        """Calibrate the device."""
        ...


__all__ = ['ICalibrate']
