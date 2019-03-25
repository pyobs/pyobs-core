from .interface import Interface


class ICooling(Interface):
    """Interface for all devices that allow for some kind of cooling."""

    def get_cooling_status(self, *args, **kwargs) -> (bool,  float, float, dict):
        """Returns the current status for the cooling.

        Returns:
            Tuple containing:
                Enabled (bool):         Whether the cooling is enabled
                SetPoint (float):       Setpoint for the cooling in celsius.
                Power (float):          Current cooling power in percent or None.
                Temperatures (dict):    Dictionary of sensor name/value pairs with temperatures
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
