from typing import Tuple

from .interface import Interface


class ILatLon(Interface):
    """Base interface for everything that can move to Lat/Lon coordinates."""
    __module__ = 'pyobs.interfaces'

    def move_latlon(self, lat: float, lon: float, *args, **kwargs):
        """Moves to given coordinates.

        Args:
            lat: Latitude in deg to move to.
            lon: Longitude in deg to move to.

        Raises:
            ValueError: If device could not move.
        """
        raise NotImplementedError

    def get_latlon(self, *args, **kwargs) -> Tuple[float, float]:
        """Returns current Latitude and Longitude.

        Returns:
            Tuple of current Latitude and Longitude in degrees.
        """
        raise NotImplementedError


__all__ = ['ILatLon']
