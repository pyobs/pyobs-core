from .IAltAz import IAltAz
from .IMotion import IMotion


class ITelescope(IMotion, IAltAz):
    """Generic interface for an astronomical telescope."""

    def track_radec(self, ra: float, dec: float, *args, **kwargs):
        """Starts tracking on given coordinates.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.

        Raises:
            ValueError: If telescope could not track.
        """
        raise NotImplementedError

    def get_radec(self, *args, **kwargs) -> (float, float):
        """Returns current RA and Dec.

        Returns:
            Tuple of current RA and Dec in degrees.
        """
        raise NotImplementedError


__all__ = ['ITelescope']
