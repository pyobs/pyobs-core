from __future__ import annotations

from typing import Any

import pytest

from pyobs.images import Image
from pyobs.robotic.utils.archive import Archive, FrameInfo
from pyobs.utils.enums import ImageType
from pyobs.utils.pipeline import Pipeline
from pyobs.utils.time import Time


def _frame(name: str, dateobs: str, exptime: float | None) -> FrameInfo:
    info = FrameInfo()
    info.filename = name
    info.dateobs = Time(dateobs)
    info.exptime = exptime
    return info


class _FakeArchive(Archive):
    """Stub archive returning a fixed list of DARK master candidates."""

    frames: list[FrameInfo] = []

    async def list_options(self, **kwargs: Any) -> dict[str, list[Any]]:
        return {}

    async def list_frames(self, **kwargs: Any) -> list[FrameInfo]:
        return self.frames

    async def download_frames(self, frames: list[FrameInfo]) -> list[Image]:
        images = []
        for frame in frames:
            image = Image()
            image.header["FNAME"] = frame.filename
            images.append(image)
        return images


@pytest.mark.asyncio
async def test_find_master_no_exptime_sorts_by_date_only() -> None:
    archive = _FakeArchive(
        frames=[
            _frame("near.fits", "2024-01-01T12:00:00", exptime=600.0),
            _frame("far.fits", "2024-01-01T00:00:00", exptime=45.0),
        ]
    )

    result = await Pipeline.find_master(
        archive, ImageType.DARK, Time("2024-01-01T12:00:01"), "cam1", "1x1", max_days=None
    )

    assert result is not None
    assert result.header["FNAME"] == "near.fits"


@pytest.mark.asyncio
async def test_find_master_exptime_match_wins_over_closer_in_time() -> None:
    archive = _FakeArchive(
        frames=[
            _frame("time-close.fits", "2024-01-01T12:00:00", exptime=999.0),
            _frame("exptime-close.fits", "2024-01-01T00:00:00", exptime=45.0),
        ]
    )

    result = await Pipeline.find_master(
        archive,
        ImageType.DARK,
        Time("2024-01-01T12:00:01"),
        "cam1",
        "1x1",
        max_days=None,
        exptime=45.0,
    )

    assert result is not None
    assert result.header["FNAME"] == "exptime-close.fits"


@pytest.mark.asyncio
async def test_find_master_exptime_ignored_for_non_dark() -> None:
    archive = _FakeArchive(
        frames=[
            _frame("time-close.fits", "2024-01-01T12:00:00", exptime=999.0),
            _frame("exptime-close.fits", "2024-01-01T00:00:00", exptime=45.0),
        ]
    )

    # exptime is only honored for DARK -- SKYFLAT still sorts by date only
    result = await Pipeline.find_master(
        archive,
        ImageType.SKYFLAT,
        Time("2024-01-01T12:00:01"),
        "cam1",
        "1x1",
        max_days=None,
        exptime=45.0,
    )

    assert result is not None
    assert result.header["FNAME"] == "time-close.fits"


@pytest.mark.asyncio
async def test_find_master_exptime_max_drops_longer_candidates() -> None:
    archive = _FakeArchive(
        frames=[
            _frame("too-long.fits", "2024-01-01T12:00:00", exptime=900.0),
            _frame("usable.fits", "2024-01-01T00:00:00", exptime=580.0),
        ]
    )

    result = await Pipeline.find_master(
        archive,
        ImageType.DARK,
        Time("2024-01-01T12:00:01"),
        "cam1",
        "1x1",
        max_days=None,
        exptime=600.0,
        exptime_max=600.0,
    )

    assert result is not None
    assert result.header["FNAME"] == "usable.fits"


@pytest.mark.asyncio
async def test_find_master_exptime_max_none_left_returns_none() -> None:
    archive = _FakeArchive(frames=[_frame("too-long.fits", "2024-01-01T12:00:00", exptime=900.0)])

    result = await Pipeline.find_master(
        archive,
        ImageType.DARK,
        Time("2024-01-01T12:00:01"),
        "cam1",
        "1x1",
        max_days=None,
        exptime=600.0,
        exptime_max=600.0,
    )

    assert result is None


@pytest.mark.asyncio
async def test_find_master_no_candidates_returns_none() -> None:
    archive = _FakeArchive(frames=[])

    result = await Pipeline.find_master(archive, ImageType.DARK, Time("2024-01-01T12:00:01"), "cam1", "1x1")

    assert result is None
