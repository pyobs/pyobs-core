from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .interface import Interface


@dataclass
class ExposureTimeState:
    exposure_time: Annotated[float, Unit.SECONDS]
    time: Time = field(default_factory=Time.now)


class IExposureTime(Interface, metaclass=ABCMeta):
    """The camera supports exposure times, to be used together with :class:`~pyobs.interfaces.ICamera`."""

    __module__ = "pyobs.interfaces"

    state = ExposureTimeState

    @abstractmethod
    async def set_exposure_time(self, exposure_time: Annotated[float, Unit.SECONDS], **kwargs: Any) -> None:
        """Set the exposure time in seconds.

        Args:
            exposure_time: Exposure time in seconds.

        Raises:
            ValueError: If exposure time could not be set.
        """
        ...


__all__ = ["IExposureTime", "ExposureTimeState"]
