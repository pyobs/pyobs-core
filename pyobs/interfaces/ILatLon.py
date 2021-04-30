from typing import Tuple

from .interface import Interface


class ILatLon(Interface):
    """The module can move to general Lat/Lon coordinates, which have to be defined by the module itself.
    Usually combined with :class:`~pyobs.interfaces.ITelescope`."""
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
