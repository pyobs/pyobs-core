from abc import ABCMeta
from typing import Any, Dict

from .IRunning import IRunning


class IAcquisition(IRunning, metaclass=ABCMeta):
    """The module can acquire a target, usually by accessing a telescope and a camera."""
    __module__ = 'pyobs.interfaces'

    async def acquire_target(self, **kwargs: Any) -> Dict[str, Any]:
        """Acquire target at given coordinates.

        If no RA/Dec are given, start from current position. Might not work for some implementations that require
        coordinates.

        Returns:
            A dictionary with entries for datetime, ra, dec, alt, az, and either off_ra, off_dec or off_alt, off_az.

        Raises:
            ValueError: If target could not be acquired.
        """
        raise NotImplementedError


__all__ = ['IAcquisition']
