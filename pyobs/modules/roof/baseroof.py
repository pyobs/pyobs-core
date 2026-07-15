from __future__ import annotations

import logging
from abc import ABCMeta
from typing import Any

from pyobs.interfaces import FitsHeaderEntry, IFitsHeaderBefore, IRoof
from pyobs.mixins import MotionStatusMixin, WeatherAwareMixin
from pyobs.modules import Module
from pyobs.utils.enums import MotionStatus

log = logging.getLogger(__name__)


class BaseRoof(WeatherAwareMixin, MotionStatusMixin, IRoof, IFitsHeaderBefore, Module, metaclass=ABCMeta):
    """Base class for roofs."""

    __module__ = "pyobs.modules.roof"

    def __init__(self, **kwargs: Any):
        """Initialize a new base roof."""
        Module.__init__(self, **kwargs)

        WeatherAwareMixin.__init__(self, **kwargs)
        MotionStatusMixin.__init__(self, **kwargs)

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        # open mixins
        await WeatherAwareMixin.open(self)
        await MotionStatusMixin.open(self)

    async def get_fits_header_before(
        self, namespaces: list[str] | None = None, **kwargs: Any
    ) -> dict[str, FitsHeaderEntry]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        return {
            "ROOF-OPN": FitsHeaderEntry(
                self.motion_status() in [MotionStatus.POSITIONED, MotionStatus.TRACKING],
                "True for open, false for closed roof",
            )
        }


__all__ = ["BaseRoof"]
