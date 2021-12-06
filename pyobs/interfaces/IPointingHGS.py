from typing import Tuple, Any

from .interface import Interface


class IPointingHGS(Interface):
    """The module can move to Mu/Psi coordinates, usually combined with :class:`~pyobs.interfaces.ITelescope`."""
    __module__ = 'pyobs.interfaces'

    async def move_hgs_lon_lat(self, lon: float, lat: float, **kwargs: Any) -> None:
        """Moves on given coordinates.

        Args:
            lon: Longitude in deg to track.
            lat: Latitude in deg to track.

        Raises:
            ValueError: If device could not move.
        """
        raise NotImplementedError

    async def get_hgs_lon_lat(self, **kwargs: Any) -> Tuple[float, float]:
        """Returns current longitude and latitude position.

        Returns:
            Tuple of current lon, lat in degrees.
        """
        raise NotImplementedError


__all__ = ['IPointingHGS']
