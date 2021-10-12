from .IRunning import IRunning


class IAcquisition(IRunning):
    """The module can acquire a target, usually by accessing a telescope and a camera."""
    __module__ = 'pyobs.interfaces'

    def acquire_target(self, exposure_time: float, *args, **kwargs) -> dict:
        """Acquire target at given coordinates.

        If no RA/Dec are given, start from current position. Might not work for some implementations that require
        coordinates.

        Args:
            exposure_time: Exposure time for acquisition in seconds.

        Returns:
            A dictionary with entries for datetime, ra, dec, alt, az, and either off_ra, off_dec or off_alt, off_az.

        Raises:
            ValueError: If target could not be acquired.
        """
        raise NotImplementedError


__all__ = ['IAcquisition']
