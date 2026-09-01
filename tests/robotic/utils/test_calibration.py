from __future__ import annotations

from typing import Any

import pytest

from pyobs.images import Image
from pyobs.robotic.utils.archive import Archive, FrameInfo
from pyobs.robotic.utils.calibration import (
    clear_cache,
    peek_cached_science_exptimes_for_night,
    science_exptimes_for_night,
)
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time


@pytest.fixture(autouse=True)
def _clear_exptime_cache() -> None:
    clear_cache()


class _FakeArchive(Archive):
    """Stub archive serving a fixed set of OBJECT frames for science_exptimes_for_night."""

    instruments: list[str] = ["cam1"]
    binnings: list[str] = ["1x1"]
    exptimes_by_frame: list[float] = []
    list_options_calls: int = 0

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
        self.list_options_calls += 1
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


# ── caching ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_second_call_hits_cache_not_archive() -> None:
    archive = _FakeArchive(exptimes_by_frame=[600.0])

    await science_exptimes_for_night(archive, site="siteA", night="2024-01-01")
    await science_exptimes_for_night(archive, site="siteA", night="2024-01-01")

    assert archive.list_options_calls == 1


@pytest.mark.asyncio
async def test_different_night_is_not_cached_together() -> None:
    archive = _FakeArchive(exptimes_by_frame=[600.0])

    await science_exptimes_for_night(archive, site="siteA", night="2024-01-01")
    await science_exptimes_for_night(archive, site="siteA", night="2024-01-02")

    assert archive.list_options_calls == 2


def test_peek_cache_returns_none_when_nothing_cached() -> None:
    archive = _FakeArchive()
    assert peek_cached_science_exptimes_for_night(archive, "siteA", "2024-01-01") is None


@pytest.mark.asyncio
async def test_peek_cache_returns_value_after_a_real_call() -> None:
    archive = _FakeArchive(exptimes_by_frame=[600.0])
    expected = await science_exptimes_for_night(archive, site="siteA", night="2024-01-01")

    assert peek_cached_science_exptimes_for_night(archive, "siteA", "2024-01-01") == expected


@pytest.mark.asyncio
async def test_peek_cache_ignores_mutation_of_the_same_archive_instance() -> None:
    """A stateful Archive field (like this fake's call counter) must not affect the cache key --
    otherwise the very first real call, which mutates that field as a side effect, would already
    miss its own cache entry on the next lookup."""
    archive = _FakeArchive(exptimes_by_frame=[600.0])

    result = await science_exptimes_for_night(archive, site="siteA", night="2024-01-01")
    assert archive.list_options_calls == 1

    assert peek_cached_science_exptimes_for_night(archive, "siteA", "2024-01-01") == result


def test_peek_cache_is_shared_across_archive_instances_of_the_same_class() -> None:
    archive_a = _FakeArchive(instruments=["cam1"])
    archive_b = _FakeArchive(instruments=["cam2"])
    import time

    from pyobs.robotic.utils import calibration

    key = calibration._cache_key(archive_a, "siteA", "2024-01-01", 0.01, 5.0)
    calibration._cache[key] = (time.monotonic(), {("cam1", "1x1"): [600.0]})

    # same class -> same key, even though instruments differ; documented limitation
    assert peek_cached_science_exptimes_for_night(archive_b, "siteA", "2024-01-01") == {("cam1", "1x1"): [600.0]}


def test_peek_cache_returns_none_once_expired() -> None:
    import time

    from pyobs.robotic.utils import calibration

    archive = _FakeArchive()
    stale = time.monotonic() - calibration._CACHE_TTL - 1.0
    key = calibration._cache_key(archive, "siteA", "2024-01-01", 0.01, 5.0)
    calibration._cache[key] = (stale, {("cam1", "1x1"): [600.0]})

    assert peek_cached_science_exptimes_for_night(archive, "siteA", "2024-01-01") is None


def test_clear_cache_empties_it() -> None:
    import time

    from pyobs.robotic.utils import calibration

    archive = _FakeArchive()
    key = calibration._cache_key(archive, "siteA", "2024-01-01", 0.01, 5.0)
    calibration._cache[key] = (time.monotonic(), {})
    assert peek_cached_science_exptimes_for_night(archive, "siteA", "2024-01-01") == {}

    clear_cache()

    assert peek_cached_science_exptimes_for_night(archive, "siteA", "2024-01-01") is None
