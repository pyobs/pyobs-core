from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


class IExposureTime(Interface, metaclass=ABCMeta):
    """The camera supports exposure times, to be used together with :class:`~pyobs.interfaces.ICamera`."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        exposure_time: Annotated[float, Unit.SECONDS]
        exposure_time_left: Annotated[float, Unit.SECONDS]
        time: Time = field(default_factory=Time.now)

    @abstractmethod
    async def set_exposure_time(self, exposure_time: Annotated[float, Unit.SECONDS], **kwargs: Any) -> None:
        """Set the exposure time in seconds.

        Args:
            exposure_time: Exposure time in seconds.

        Raises:
            ValueError: If exposure time could not be set.
        """
        ...

    @abstractmethod
    async def get_exposure_time(self, **kwargs: Any) -> Annotated[float, Unit.SECONDS]:
        """Returns the exposure time in seconds.

        Returns:
            Exposure time in seconds.
        """
        ...

    @abstractmethod
    async def get_exposure_time_left(self, **kwargs: Any) -> Annotated[float, Unit.SECONDS]:
        """Returns the remaining exposure time on the current exposure in seconds.

        Returns:
            Remaining exposure time in seconds.
        """
        ...


__all__ = ["IExposureTime"]
