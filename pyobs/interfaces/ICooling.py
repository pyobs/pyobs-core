from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Annotated, Any

from ..utils.enums import Unit
from ..utils.time import Time
from .ITemperatures import ITemperatures


class ICooling(ITemperatures, metaclass=ABCMeta):
    """The module can control the cooling of a device."""

    __module__ = "pyobs.interfaces"

    @dataclass
    class State:
        setpoint: Annotated[float, Unit.CELSIUS] | None
        power: Annotated[int, Unit.PERCENT] | None
        enabled: bool
        time: Time = field(default_factory=Time.now)

    @abstractmethod
    async def set_cooling(self, enabled: bool, setpoint: Annotated[float, Unit.CELSIUS], **kwargs: Any) -> None:
        """Enables/disables cooling and sets setpoint.

        Args:
            enabled: Enable or disable cooling.
            setpoint: Setpoint in celsius for the cooling.

        Raises:
            ValueError: If cooling could not be set.
        """
        ...


__all__ = ["ICooling"]
