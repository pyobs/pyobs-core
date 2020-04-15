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
            'ROOF-OPN': (self.get_motion_status() in [IMotion.Status.POSITIONED, IMotion.Status.TRACKING],
                         'True for open, false for closed roof')
        }

    def is_ready(self, *args, **kwargs) -> bool:
        """Returns the device is "ready", whatever that means for the specific device.

        Returns:
            True, if roof is open.
        """

        # check that motion is not in one of the states listed below
        return self.get_motion_status() not in [IMotion.Status.PARKED, IMotion.Status.INITIALIZING,
                                                IMotion.Status.PARKING, IMotion.Status.ERROR, IMotion.Status.UNKNOWN]


__all__ = ['BaseRoof']
