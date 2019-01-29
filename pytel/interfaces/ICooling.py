from .IStatus import IStatus


class ICooling(IStatus):
    """Interface for all devices that allow for some kind of cooling."""

    def status(self, *args, **kwargs) -> dict:
        """Returns the current status for the cooling.

        Returns:
            dict: A dictionary that should contain at least the following fields:

                ICooling:
                    Enabled (bool):         Whether the cooling is enabled
                    SetPoint (float):       Setpoint for the cooling in celsius.
                    Power (float):          Current cooling power in percent or None.
                    Temperatures (dict):    Dictionary of sensor name/value pairs with temperatures
                        <sensor> (float):   Sensor value
        """
        raise NotImplementedError

    def set_cooling(self, enabled: bool, setpoint: float, *args, **kwargs) -> bool:
        """Enables/disables cooling and sets setpoint.

        Args:
            enabled (bool): Enable or disable cooling.
            setpoint (float): Setpoint in celsius for the cooling.

        Returns:
            bool: True if successful, otherwise False.
        """
        raise NotImplementedError


__all__ = ['ICooling']
