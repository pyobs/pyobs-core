from .IMotion import IMotion


class ITelescope(IMotion):
    """
    Generic interface for an astronomical telescope.

    Other interfaces to be implemented:
        (none)
    """

    def init(self, *args, **kwargs):
        """Initialize telescope.

        Raises:
            ValueError: If telescope could not be initialized.
        """
        raise NotImplementedError

    def park(self, *args, **kwargs):
        """Park telescope.

        Raises:
            ValueError: If telescope could not be parked.
        """
        raise NotImplementedError

    def track(self, ra: float, dec: float, *args, **kwargs):
        """Starts tracking on given coordinates.

        Args:
            ra: RA in deg to track.
            dec: Dec in deg to track.

        Raises:
            ValueError: If telescope could not track.
        """
        raise NotImplementedError

    def move(self, alt: float, az: float, *args, **kwargs):
        """Moves to given coordinates.

        Args:
            alt: Alt in deg to move to.
            az: Az in deg to move to.

        Raises:
            ValueError: If telescope could not move.
        """
        raise NotImplementedError

    def offset(self, dalt: float, daz: float, *args, **kwargs):
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

    def status(self, *args, **kwargs) -> dict:
        """Returns current status.

        Returns:
            dict: A dictionary that should contain at least the following fields:

                ITelescope:
                    Status (str):       Current status of telescope (IDLE, SLEWING, etc)
                    Position:
                        RA (float):     Right ascension [degrees]
                        Dec (float):    Declination [degrees]
                        Alt (float):    Altitude [degrees]
                        Az (float):     Azimuth [degrees]
                    Temperatures:
                        <sensor>: float
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
