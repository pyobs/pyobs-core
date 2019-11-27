import logging
import typing

from pyobs.events import MotionStatusChangedEvent
from pyobs.interfaces import IRoof, IMotion, IWeather, IFitsHeaderProvider
from pyobs import PyObsModule
from pyobs.mixins import MotionStatusMixin, WeatherAwareMixin


log = logging.getLogger(__name__)


class BaseRoof(WeatherAwareMixin, MotionStatusMixin, IRoof, IFitsHeaderProvider, PyObsModule):
    """Base class for roofs."""

    def __init__(self, *args, **kwargs):
        """Initialize a new base roof."""
        PyObsModule.__init__(self, *args, **kwargs)

        # init mixins
        WeatherAwareMixin.__init__(self, *args, **kwargs)
        MotionStatusMixin.__init__(self, *args, **kwargs)

    def open(self):
        """Open module."""
        PyObsModule.open(self)

        # open mixins
        WeatherAwareMixin.open(self)
        MotionStatusMixin.open(self)

    def get_fits_headers(self, namespaces: list = None, *args, **kwargs) -> dict:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        return {
            'ROOF-OPN': (self._motion_status in [IMotion.Status.POSITIONED, IMotion.Status.TRACKING],
                         'True for open, false for closed roof')
        }


__all__ = ['BaseRoof']
