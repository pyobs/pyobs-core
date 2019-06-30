from .interface import Interface


class IAltAzMount(Interface):
    """Telescopes on an altaz mount should also implement this interface."""

    def offset_altaz(self, dalt: float, daz: float, *args, **kwargs):
        """Move an Alt/Az offset.

        Args:
            dalt: Altitude offset in degrees.
            daz: Azimuth offset in degrees.

        Raises:
            ValueError: If offset could not be set.
        """
        raise NotImplementedError

    def get_offset_altaz(self, *args, **kwargs) -> (float, float):
        """Get Alt/Az offset.

        Returns:
            Tuple with alt and az offsets.
        """
        raise NotImplementedError


__all__ = ['IAltAzMount']
