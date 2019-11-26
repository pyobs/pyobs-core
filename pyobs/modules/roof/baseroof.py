import logging
import typing

from pyobs.events import MotionStatusChangedEvent
from pyobs.interfaces import IRoof, IMotion, IWeather, IFitsHeaderProvider
from pyobs import PyObsModule
from pyobs.mixins.weatheraware import WeatherAwareMixin


log = logging.getLogger(__name__)


class BaseRoof(WeatherAwareMixin, IRoof, IFitsHeaderProvider, PyObsModule):
    """Base class for roofs."""

    def __init__(self, *args, **kwargs):
        """Initialize a new base roof."""
        PyObsModule.__init__(self, *args, **kwargs)

        # status
        self._motion_status = IMotion.Status.PARKED

        # init WeatherAware
        WeatherAwareMixin.__init__(self, *args, **kwargs)

    def open(self):
        """Open module."""
        PyObsModule.open(self)

        # subscribe to events
        if self.comm:
            self.comm.register_event(MotionStatusChangedEvent)

        # same for WeatherAware
        WeatherAwareMixin.open(self)

    def _change_motion_status(self, status: IMotion.Status):
        """Change motion status and send event,

        Args:
            status: New motion status.
        """

        # send event, if it changed
        if self._motion_status != status:
            self.comm.send_event(MotionStatusChangedEvent(self._motion_status, status))

        # set it
        self._motion_status = status

    def get_motion_status(self, device: str = None) -> IMotion.Status:
        """Returns current motion status.

        Args:
            device: Name of device to get status for, or None.

        Returns:
            A string from the Status enumerator.
        """
        return self._motion_status

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
