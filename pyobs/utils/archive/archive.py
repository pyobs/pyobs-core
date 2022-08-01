from __future__ import annotations
from typing import List, Optional, Dict, Any, TYPE_CHECKING

from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.images import Image


class FrameInfo:
    """Base class for frame infos."""

    def __init__(self) -> None:
        self.id = None
        self.filename = None
        self.filter_name = None
        self.binning = None
        self.dateobs = None


class Archive:
    """Base class for image archives."""

    __module__ = "pyobs.utils.archive"

    async def list_options(
        self,
        start: Optional[Time] = None,
        end: Optional[Time] = None,
        night: Optional[str] = None,
        site: Optional[str] = None,
        telescope: Optional[str] = None,
        instrument: Optional[str] = None,
        image_type: Optional[ImageType] = None,
        binning: Optional[str] = None,
        filter_name: Optional[str] = None,
        rlevel: Optional[int] = None,
    ) -> Dict[str, List[Any]]:
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
        start: Optional[Time] = None,
        end: Optional[Time] = None,
        night: Optional[str] = None,
        site: Optional[str] = None,
        telescope: Optional[str] = None,
        instrument: Optional[str] = None,
        image_type: Optional[ImageType] = None,
        binning: Optional[str] = None,
        filter_name: Optional[str] = None,
        rlevel: Optional[int] = None,
    ) -> List[FrameInfo]:
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

    async def download_frames(self, frames: List[FrameInfo]) -> List[Image]:
        """Download given frames.

        Args:
            frames: List of frames to download.

        Returns:
            List of Image objects.
        """
        raise NotImplementedError

    async def upload_frames(self, frames: List[Image]) -> None:
        raise NotImplementedError


__all__ = ["FrameInfo", "Archive"]
