from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from pyobs.utils.enums import ImageType


@dataclass
class MasterCalibCreated:
    """A master calibration frame (BIAS/DARK/SKYFLAT) was created and stored/uploaded."""

    image_type: ImageType
    instrument: str
    binning: str
    filter_name: str | None
    filename: str
    exptime: float | None = None
    """The dark's exposure time in seconds, for a per-exptime DARK master. None for BIAS/SKYFLAT
    and for a DARK master created before per-exptime grouping existed."""


@dataclass
class ScienceFrameProcessed:
    """One science frame finished processing (successfully or not).

    index/total are cumulative across the whole reduction run, not just the current
    instrument/binning/filter batch.
    """

    index: int
    total: int
    filename: str | None
    status: Literal["ok", "error"]
    error: str | None = None


ProgressEvent = MasterCalibCreated | ScienceFrameProcessed
ProgressCallback = Callable[[ProgressEvent], None]


__all__ = ["MasterCalibCreated", "ScienceFrameProcessed", "ProgressEvent", "ProgressCallback"]
