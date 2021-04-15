from typing import Tuple

from .ITemperatures import ITemperatures


class ICooling(ITemperatures):
    """Interface for all devices that allow for some kind of cooling."""
    __module__ = 'pyobs.interfaces'

    def get_cooling_status(self, *args, **kwargs) -> Tuple[bool, float, float]:
        """Returns the current status for the cooling.

        Returns:
            (tuple): Tuple containing:
                Enabled:  Whether the cooling is enabled
                SetPoint: Setpoint for the cooling in celsius.
                Power:    Current cooling power in percent or None.
        """
        raise NotImplementedError

    def set_cooling(self, enabled: bool, setpoint: float, *args, **kwargs):
        """Enables/disables cooling and sets setpoint.

        Args:
            enabled: Enable or disable cooling.
            setpoint: Setpoint in celsius for the cooling.

        Raises:
            ValueError: If cooling could not be set.
        """
        raise NotImplementedError


__all__ = ['ICooling']
