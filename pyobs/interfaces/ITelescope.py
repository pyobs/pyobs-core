from .IMotion import IMotion


class ITelescope(IMotion):
    """
    Generic interface for an astronomical telescope.

    Other interfaces to be implemented:
        (none)
    """

    def track_radec(self, ra: float, dec: float, *args, **kwargs):
        """Starts tracking on given coordinates.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.

        Raises:
            ValueError: If telescope could not track.
        """
        raise NotImplementedError

    def move_altaz(self, alt: float, az: float, *args, **kwargs):
        """Moves to given coordinates.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.

        Raises:
            ValueError: If telescope could not move.
        """
        raise NotImplementedError

    def offset_altaz(self, dalt: float, daz: float, *args, **kwargs):
        """Move an Alt/Az offset, which will be reset on next call of track.

        Args:
            dalt: Altitude offset in degrees.
            daz: Azimuth offset in degrees.

        Raises:
            ValueError: If offset could not be set.
        """
        raise NotImplementedError

    def reset_offset(self, *args, **kwargs):
        """Reset Alt/Az offset.

        Raises:
            ValueError: If offset could not be reset.
        """
        raise NotImplementedError

    def get_ra_dec(self) -> (float, float):
        """Returns current RA and Dec.

        Returns:
            Tuple of current RA and Dec in degrees.
        """
        raise NotImplementedError

    def get_alt_az(self) -> (float, float):
        """Returns current Alt and Az.

        Returns:
            Tuple of current Alt and Az in degrees.
        """
        raise NotImplementedError


__all__ = ['ITelescope']
