from typing import Tuple

from .interface import Interface


class IAltAz(Interface):
    """Base interface for everything that can move to Alt/Az coordinates."""

    def move_altaz(self, alt: float, az: float, *args, **kwargs):
        """Moves to given coordinates.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.

        Raises:
            ValueError: If device could not move.
        """
        raise NotImplementedError

    def get_altaz(self, *args, **kwargs) -> Tuple[float, float]:
        """Returns current Alt and Az.

        Returns:
            Tuple of current Alt and Az in degrees.
        """
        raise NotImplementedError


__all__ = ['IAltAz']
