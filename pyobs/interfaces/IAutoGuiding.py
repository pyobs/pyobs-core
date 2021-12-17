from abc import ABCMeta, abstractmethod
from typing import Any

from .IStartStop import IStartStop


class IAutoGuiding(IStartStop, metaclass=ABCMeta):
    """The module can perform auto-guiding."""
    __module__ = 'pyobs.interfaces'

    @abstractmethod
    async def set_exposure_time(self, exposure_time: float, **kwargs: Any) -> None:
        """Set the exposure time for the auto-guider.

        Args:
            exposure_time: Exposure time in secs.
        """
        ...


__all__ = ['IAutoGuiding']
