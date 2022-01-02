import logging
from abc import ABCMeta
from typing import List, Dict, Tuple, Any, Optional

from pyobs.interfaces import IRoof, IFitsHeaderBefore
from pyobs.modules import Module
from pyobs.mixins import MotionStatusMixin, WeatherAwareMixin
from pyobs.utils.enums import MotionStatus

log = logging.getLogger(__name__)


class BaseRoof(WeatherAwareMixin, MotionStatusMixin, IRoof, IFitsHeaderBefore, Module, metaclass=ABCMeta):
    """Base class for roofs."""

    __module__ = "pyobs.modules.roof"

    def __init__(self, **kwargs: Any):
        """Initialize a new base roof."""
        Module.__init__(self, **kwargs)

        # init mixins
        WeatherAwareMixin.__init__(self, **kwargs)
        MotionStatusMixin.__init__(self, **kwargs)

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # open mixins
        await WeatherAwareMixin.open(self)
        await MotionStatusMixin.open(self)

    async def get_fits_header_before(
        self, namespaces: Optional[List[str]] = None, **kwargs: Any
    ) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        return {
            "ROOF-OPN": (
                await self.get_motion_status() in [MotionStatus.POSITIONED, MotionStatus.TRACKING],
                "True for open, false for closed roof",
            )
        }

    async def is_ready(self, **kwargs: Any) -> bool:
        """Returns the device is "ready", whatever that means for the specific device.

        Returns:
            True, if roof is open.
        """

        # check that motion is not in one of the states listed below
        return await self.get_motion_status() not in [
            MotionStatus.PARKED,
            MotionStatus.INITIALIZING,
            MotionStatus.PARKING,
            MotionStatus.ERROR,
            MotionStatus.UNKNOWN,
        ]


__all__ = ["BaseRoof"]
