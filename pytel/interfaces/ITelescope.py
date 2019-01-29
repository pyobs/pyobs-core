from .IStatus import IStatus


class ITelescope(IStatus):
    def init(self, *args, **kwargs) -> bool:
        """Initialize telescope.

        Returns:
            (bool) Success
        """
        raise NotImplementedError

    def park(self, *args, **kwargs) -> bool:
        """Park telescope.

        Returns:
            (bool) Success
        """
        raise NotImplementedError

    def track(self, ra: float, dec: float, *args, **kwargs) -> bool:
        """starts tracking on given coordinates"""
        raise NotImplementedError

    def move(self, alt: float, az: float, *args, **kwargs) -> bool:
        """moves to given coordinates"""
        raise NotImplementedError

    def offset(self, dalt: float, daz: float, *args, **kwargs) -> bool:
        """Move an Alt/Az offset, which will be reset on next call of track.

        Args:
            dalt: Altitude offset in degrees.
            daz: Azimuth offset in degrees.
        """
        raise NotImplementedError

    def reset_offset(self, *args, **kwargs) -> bool:
        """Reset Alt/Az offset."""
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


__all__ = ['ITelescope']
