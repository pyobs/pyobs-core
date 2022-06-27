from abc import ABCMeta, abstractmethod
from typing import Tuple, Any

from .ITemperatures import ITemperatures


class ICooling(ITemperatures, metaclass=ABCMeta):
    """The module can control the cooling of a device."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def get_cooling(self, **kwargs: Any) -> Tuple[bool, float, float]:
        """Returns the current status for the cooling.

        Returns:
            (tuple): Tuple containing:
                Enabled:  Whether the cooling is enabled
                SetPoint: Setpoint for the cooling in celsius.
                Power:    Current cooling power in percent or None.
        """
        ...

    @abstractmethod
    async def set_cooling(self, enabled: bool, setpoint: float, **kwargs: Any) -> None:
        """Enables/disables cooling and sets setpoint.

        Args:
            enabled: Enable or disable cooling.
            setpoint: Setpoint in celsius for the cooling.

        Raises:
            ValueError: If cooling could not be set.
        """
        ...


__all__ = ["ICooling"]
