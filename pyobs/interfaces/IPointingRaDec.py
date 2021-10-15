from typing import Tuple

from .interface import Interface


class IPointingRaDec(Interface):
    """The module can move to RA/Dec coordinates, usually combined with :class:`~pyobs.interfaces.ITelescope`."""
    __module__ = 'pyobs.interfaces'

    def move_radec(self, ra: float, dec: float, track: bool = True, *args, **kwargs):
        """Starts tracking on given coordinates.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.
            track: Whether the device should start tracking on the given coordinates.

        Raises:
            ValueError: If device could not track.
        """
        raise NotImplementedError

    def get_radec(self, *args, **kwargs) -> Tuple[float, float]:
        """Returns current RA and Dec.

        Returns:
            Tuple of current RA and Dec in degrees.
        """
        raise NotImplementedError


__all__ = ['IPointingRaDec']
