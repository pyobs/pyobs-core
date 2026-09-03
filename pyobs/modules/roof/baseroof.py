from __future__ import annotations

import logging
from abc import ABCMeta
from typing import Any

from pyobs.interfaces import FitsHeaderEntry, IFitsHeaderBefore, IRoof
from pyobs.mixins import MotionStatusMixin, WeatherAwareMixin
from pyobs.modules import Module
from pyobs.utils.enums import MotionStatus
from pyobs.utils.versions import version_fits_headers

log = logging.getLogger(__name__)


class BaseRoof(Module, WeatherAwareMixin, MotionStatusMixin, IRoof, IFitsHeaderBefore, metaclass=ABCMeta):
    """Base class for roofs."""

    __module__ = "pyobs.modules.roof"

    def __init__(self, **kwargs: Any):
        """Initialize a new base roof."""
        super().__init__(**kwargs)

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
        hdr: dict[str, FitsHeaderEntry] = {
            "ROOF-OPN": FitsHeaderEntry(
                self.motion_status() in [MotionStatus.POSITIONED, MotionStatus.TRACKING],
                "True for open, false for closed roof",
            )
        }
        hdr.update(version_fits_headers(self.name))
        return hdr


__all__ = ["BaseRoof"]
