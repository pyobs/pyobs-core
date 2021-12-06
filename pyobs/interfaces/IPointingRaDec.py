from typing import Tuple, Any

from .interface import Interface


class IPointingRaDec(Interface):
    """The module can move to RA/Dec coordinates, usually combined with :class:`~pyobs.interfaces.ITelescope`."""
    __module__ = 'pyobs.interfaces'

    async def move_radec(self, ra: float, dec: float, **kwargs: Any) -> None:
        """Starts tracking on given coordinates.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.

        Raises:
            ValueError: If device could not track.
        """
        raise NotImplementedError

    async def get_radec(self, **kwargs: Any) -> Tuple[float, float]:
        """Returns current RA and Dec.

        Returns:
            Tuple of current RA and Dec in degrees.
        """
        raise NotImplementedError


__all__ = ['IPointingRaDec']
