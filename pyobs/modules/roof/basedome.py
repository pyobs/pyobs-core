import logging

from pyobs.interfaces import IDome
from .baseroof import BaseRoof


log = logging.getLogger(__name__)


class BaseDome(IDome, BaseRoof):
    """Base class for domes."""

    def __init__(self, *args, **kwargs):
        """Initialize a new base dome."""
        BaseRoof.__init__(self, *args, **kwargs)

    def get_fits_headers(self, namespaces: list = None, *args, **kwargs) -> dict:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """

        # get from parent
        hdr = BaseRoof.get_fits_headers(self, namespaces, *args, **kwargs)

        # add azimuth and return it
        _, az = self.get_altaz()
        hdr['ROOF-AZ'] = (az, 'Azimuth of roof slit, deg E of N')
        return hdr


__all__ = ['BaseDome']
