from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from pyobs.images import Image
from pyobs.object import get_object
from pyobs.robotic.utils.archive import Archive
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time

from .pipeline import Pipeline
from .progress import ProgressCallback, ProgressEvent

log = logging.getLogger(__name__)


class ReductionBase(ABC):
    """Common base for classes that reduce one observation period's worth of data.

    Holds the archive/pipeline plumbing, the master-calibration-frame cache and lookup
    (shared by any reduction strategy that needs BIAS/DARK/SKYFLAT masters), and the
    progress-callback mechanism. Concrete subclasses implement __call__.
    """

    def __init__(
        self,
        archive: dict[str, Any] | Archive,
        pipeline: dict[str, Any] | Pipeline,
        min_flats: int = 10,
        progress_callback: ProgressCallback | None = None,
    ):
        """
        Args:
            archive: Archive to fetch raw and calibration frames from.
            pipeline: Science pipeline.
            min_flats: Minimum number of raw frames to create flat field.
            progress_callback: Optional callable invoked with a ProgressEvent whenever a
                master calibration frame is created or a science frame finishes processing.
                Exceptions raised by the callback are logged and otherwise ignored.
        """
        self._archive = get_object(archive, Archive)
        self._pipeline = get_object(pipeline, Pipeline, archive=archive)
        self._min_flats = min_flats
        self._progress_callback = progress_callback

        # cache for master calibration frames -- exptime is None for every non-DARK type, and
        # the grouped exptime for DARK (a night can have darks at more than one exposure time)
        self._master_frames: dict[tuple[ImageType, str, str, str | None, float | None], Image] = {}

    def _report_progress(self, event: ProgressEvent) -> None:
        if self._progress_callback is None:
            return
        try:
            self._progress_callback(event)
        except Exception:
            log.exception("Error in progress callback.")

    async def _find_master(
        self,
        night: str,
        image_type: ImageType,
        instrument: str,
        binning: str,
        filter_name: str | None = None,
        max_days: float = 30.0,
        exptime: float | None = None,
        exptime_tolerance: float = 0.01,
    ) -> Image | None:
        """Find master calibration frame for given parameters using a cache.

        Args:
            image_type: image type.
            instrument: Instrument name.
            binning: Binning.
            filter_name: Name of filter.
            max_days: Maximum number of days from DATE-OBS to find frames.
            exptime: For DARK, prefer a master close to this exposure time; see
                Pipeline.find_master. Also used as part of the cache key, so lookups at
                different exptimes don't collide.
            exptime_tolerance: See Pipeline.find_master.

        Returns:
            Image or None
        """

        # is in cache?
        if (image_type, instrument, binning, filter_name, exptime) in self._master_frames:
            return self._master_frames[image_type, instrument, binning, filter_name, exptime]

        # try to download one
        midnight = Time(night + " 23:59:59")
        image = await self._pipeline.find_master(
            self._archive,
            image_type,
            midnight,
            instrument,
            binning,
            filter_name,
            max_days=max_days,
            exptime=exptime,
            exptime_tolerance=exptime_tolerance,
        )
        if image is not None:
            # store and return it
            self._master_frames[image_type, instrument, binning, filter_name, exptime] = image
            return image
        else:
            # still nothing
            return None

    @abstractmethod
    async def __call__(self, site: str, night: str) -> None:
        """Reduces all data for the given site and observation period."""
        ...


__all__ = ["ReductionBase"]
