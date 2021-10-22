import logging
from typing import List, Dict, Tuple, Any

from pyobs.interfaces import IRoof, IFitsHeaderProvider
from pyobs.modules import Module
from pyobs.mixins import MotionStatusMixin, WeatherAwareMixin
from pyobs.utils.enums import MotionStatus

log = logging.getLogger(__name__)


class BaseRoof(WeatherAwareMixin, MotionStatusMixin, IRoof, IFitsHeaderProvider, Module):
    """Base class for roofs."""
    __module__ = 'pyobs.modules.roof'

    def __init__(self, **kwargs: Any):
        """Initialize a new base roof."""
        Module.__init__(self, **kwargs)

        # init mixins
        WeatherAwareMixin.__init__(self, **kwargs)
        MotionStatusMixin.__init__(self, **kwargs)

    def open(self) -> None:
        """Open module."""
        Module.open(self)

        # open mixins
        WeatherAwareMixin.open(self)
        MotionStatusMixin.open(self)

    def get_fits_headers(self, namespaces: List[str] = None, **kwargs: Any) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        return {
            'ROOF-OPN': (self.get_motion_status() in [MotionStatus.POSITIONED, MotionStatus.TRACKING],
                         'True for open, false for closed roof')
        }

    def is_ready(self, **kwargs: Any) -> bool:
        """Returns the device is "ready", whatever that means for the specific device.

        Returns:
            True, if roof is open.
        """

        # check that motion is not in one of the states listed below
        return self.get_motion_status() not in [MotionStatus.PARKED, MotionStatus.INITIALIZING,
                                                MotionStatus.PARKING, MotionStatus.ERROR, MotionStatus.UNKNOWN]


__all__ = ['BaseRoof']
