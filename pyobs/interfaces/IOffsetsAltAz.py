from typing import Tuple, Any

from .interface import Interface


class IOffsetsAltAz(Interface):
    """The module supports Alt/Az offsets, usually combined with :class:`~pyobs.interfaces.ITelescope` and
    :class:`~pyobs.interfaces.IAltAz`."""
    __module__ = 'pyobs.interfaces'

    async def set_offsets_altaz(self, dalt: float, daz: float, **kwargs: Any) -> None:
        """Move an Alt/Az offset.

        Args:
            dalt: Altitude offset in degrees.
            daz: Azimuth offset in degrees.

        Raises:
            ValueError: If offset could not be set.
        """
        raise NotImplementedError

    async def get_offsets_altaz(self, **kwargs: Any) -> Tuple[float, float]:
        """Get Alt/Az offset.

        Returns:
            Tuple with alt and az offsets.
        """
        raise NotImplementedError


__all__ = ['IOffsetsAltAz']
