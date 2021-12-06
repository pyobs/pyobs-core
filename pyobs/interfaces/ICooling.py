from typing import Tuple, Any

from .ITemperatures import ITemperatures


class ICooling(ITemperatures):
    """The module can control the cooling of a device."""
    __module__ = 'pyobs.interfaces'

    async def get_cooling_status(self, **kwargs: Any) -> Tuple[bool, float, float]:
        """Returns the current status for the cooling.

        Returns:
            (tuple): Tuple containing:
                Enabled:  Whether the cooling is enabled
                SetPoint: Setpoint for the cooling in celsius.
                Power:    Current cooling power in percent or None.
        """
        raise NotImplementedError

    async def set_cooling(self, enabled: bool, setpoint: float, **kwargs: Any) -> None:
        """Enables/disables cooling and sets setpoint.

        Args:
            enabled: Enable or disable cooling.
            setpoint: Setpoint in celsius for the cooling.

        Raises:
            ValueError: If cooling could not be set.
        """
        raise NotImplementedError


__all__ = ['ICooling']
