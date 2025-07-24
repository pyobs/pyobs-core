from __future__ import annotations
from typing import Any, TYPE_CHECKING

from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.images import Image


class FrameInfo:
    """Base class for frame infos."""

    def __init__(self) -> None:
        self.id: str | int | None = None
        self.filename: str | None = None
        self.filter_name: str | None = None
        self.binning: int | None = None
        self.dateobs: str | None = None


class Archive:
    """Base class for image archives."""

    __module__ = "pyobs.utils.archive"

    async def list_options(
        self,
        start: Time | None = None,
        end: Time | None = None,
        night: str | None = None,
        site: str | None = None,
        telescope: str | None = None,
        instrument: str | None = None,
        image_type: ImageType | None = None,
        binning: str | None = None,
        filter_name: str | None = None,
        rlevel: int | None = None,
    ) -> dict[str, list[Any]]:
        """Returns a list of options restricted to the given parameters.

        Args:
            start: Start time for restriction.
            end: End time for restriction.
            night: Images in given night.
            site: From given site.
            telescope: From given telescope.
            instrument: From given instrument.
            image_type: With given image type.
            binning: With given binning.
            filter_name: With given filter.
            rlevel: In given reduction level.

        Returns:
            Dictionary with lists of "binnings", "filters", "imagetypes", "instruments", "sites", and "telescopes".
        """
        raise NotImplementedError

    async def list_frames(
        self,
        start: Time | None = None,
        end: Time | None = None,
        night: str | None = None,
        site: str | None = None,
        telescope: str | None = None,
        instrument: str | None = None,
        image_type: ImageType | None = None,
        binning: str | None = None,
        filter_name: str | None = None,
        rlevel: int | None = None,
    ) -> list[FrameInfo]:
        """Returns a list of frames restricted to the given parameters.

        Args:
            start: Start time for restriction.
            end: End time for restriction.
            night: Images in given night.
            site: From given site.
            telescope: From given telescope.
            instrument: From given instrument.
            image_type: With given image type.
            binning: With given binning.
            filter_name: With given filter.
            rlevel: In given reduction level.

        Returns:
            List of frames.
        """
        raise NotImplementedError

    async def download_frames(self, frames: list[FrameInfo]) -> list[Image]:
        """Download given frames.

        Args:
            frames: List of frames to download.

        Returns:
            List of Image objects.
        """
        raise NotImplementedError

    async def upload_frames(self, frames: list[Image]) -> None:
        raise NotImplementedError


__all__ = ["FrameInfo", "Archive"]
