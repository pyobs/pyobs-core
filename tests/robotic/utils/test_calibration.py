from __future__ import annotations

from typing import Any

import pytest

from pyobs.images import Image
from pyobs.robotic.utils.archive import Archive, FrameInfo
from pyobs.robotic.utils.calibration import science_exptimes_for_night
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time


class _FakeArchive(Archive):
    """Stub archive serving a fixed set of OBJECT frames for science_exptimes_for_night."""

    instruments: list[str] = ["cam1"]
    binnings: list[str] = ["1x1"]
    exptimes_by_frame: list[float] = []

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
        obsnum: str | None = None,
        exptime: float | None = None,
    ) -> dict[str, list[Any]]:
        return {"instruments": self.instruments, "binnings": self.binnings}

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
        obsnum: str | None = None,
        exptime: float | None = None,
    ) -> list[FrameInfo]:
        frames = []
        for e in self.exptimes_by_frame:
            info = FrameInfo()
            info.exptime = e
            frames.append(info)
        return frames

    async def download_frames(self, frames: list[FrameInfo]) -> list[Image]:
        return []


@pytest.mark.asyncio
async def test_groups_exptimes_per_instrument_binning() -> None:
    archive = _FakeArchive(instruments=["cam1"], binnings=["1x1"], exptimes_by_frame=[30.0, 30.1, 600.0])

    result = await science_exptimes_for_night(archive, site="siteA", night="2024-01-01")

    assert result == {("cam1", "1x1"): [30.05, 600.0]}


@pytest.mark.asyncio
async def test_multiple_instrument_binning_combinations() -> None:
    archive = _FakeArchive(instruments=["cam1", "cam2"], binnings=["1x1"], exptimes_by_frame=[45.0])

    result = await science_exptimes_for_night(archive, site="siteA", night="2024-01-01")

    assert set(result.keys()) == {("cam1", "1x1"), ("cam2", "1x1")}
    assert result[("cam1", "1x1")] == [45.0]


@pytest.mark.asyncio
async def test_drops_exptimes_below_min_exptime() -> None:
    archive = _FakeArchive(instruments=["cam1"], binnings=["1x1"], exptimes_by_frame=[2.0, 4.0, 30.0])

    result = await science_exptimes_for_night(archive, site="siteA", night="2024-01-01", min_exptime=5.0)

    assert result == {("cam1", "1x1"): [30.0]}


@pytest.mark.asyncio
async def test_min_exptime_none_keeps_every_exptime() -> None:
    archive = _FakeArchive(instruments=["cam1"], binnings=["1x1"], exptimes_by_frame=[2.0, 30.0])

    result = await science_exptimes_for_night(archive, site="siteA", night="2024-01-01", min_exptime=None)

    assert result == {("cam1", "1x1"): [2.0, 30.0]}


@pytest.mark.asyncio
async def test_empty_night_returns_empty_dict() -> None:
    archive = _FakeArchive(instruments=["cam1"], binnings=["1x1"], exptimes_by_frame=[])

    result = await science_exptimes_for_night(archive, site="siteA", night="2024-01-01")

    assert result == {}
