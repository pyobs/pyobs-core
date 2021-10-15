from typing import Tuple

from .interface import Interface


class IOffsetsAltAz(Interface):
    """The module supports Alt/Az offsets, usually combined with :class:`~pyobs.interfaces.ITelescope` and
    :class:`~pyobs.interfaces.IAltAz`."""
    __module__ = 'pyobs.interfaces'

    def set_altaz_offsets(self, dalt: float, daz: float, *args, **kwargs):
        """Move an Alt/Az offset.

        Args:
            dalt: Altitude offset in degrees.
            daz: Azimuth offset in degrees.

        Raises:
            ValueError: If offset could not be set.
        """
        raise NotImplementedError

    def get_altaz_offsets(self, *args, **kwargs) -> Tuple[float, float]:
        """Get Alt/Az offset.

        Returns:
            Tuple with alt and az offsets.
        """
        raise NotImplementedError


__all__ = ['IOffsetsAltAz']
