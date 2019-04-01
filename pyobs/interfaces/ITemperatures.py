from .interface import Interface


class ITemperatures(Interface):
    """Interface for all devices that measure temperatures."""

    def get_temperatures(self, *args, **kwargs) -> dict:
        """Returns all temperatures measured by this module.

        Returns:
            Dict containing temperatures.
        """
        raise NotImplementedError


__all__ = ['ITemperatures']
