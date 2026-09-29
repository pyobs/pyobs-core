"""Tests for the guiding frame sources, see specs/design/guiding-raw-stream.md."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pytest
import pytest_asyncio
from aiohttp.test_utils import TestServer

from pyobs.comm import Comm
from pyobs.modules.camera.basevideo import BaseVideo
from pyobs.modules.camera.videoframes import Frame
from pyobs.modules.pointing.guidingsource import RawStreamSource, crop_around_brightest_star
from pyobs.utils.time import Time
from tests.helpers import make_proxy_cm


@pytest_asyncio.fixture
async def video_server() -> AsyncIterator[tuple[BaseVideo, str]]:
    video = BaseVideo(comm=MagicMock(spec=Comm))
    server = TestServer(video._app)
    await server.start_server()
    try:
        yield video, str(server.make_url("/video.raw"))
    finally:
        await server.close()


def make_source(url: str, **kwargs: Any) -> RawStreamSource:
    module = MagicMock()
    module._comm = None  # no peers to request FITS headers from
    module.comm.name = "guider"
    module.vfs.open_file.return_value = SimpleNamespace(url=url, headers={})
    module.safe_proxy = MagicMock(return_value=make_proxy_cm(None))
    return RawStreamSource(module, "camera", path="/webcam/video.raw", **kwargs)


def star_frame(x: int, y: int, shape: tuple[int, int] = (100, 120)) -> np.ndarray:
    rng = np.random.default_rng(42)
    yy, xx = np.mgrid[: shape[0], : shape[1]]
    star = 20000.0 * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * 2.0**2))
    return (1000 + rng.normal(0, 10, shape) + star).astype(np.uint16)


async def add_later(video: BaseVideo, frames: list[Frame], delay: float = 0.05) -> None:
    for frame in frames:
        await asyncio.sleep(delay)
        await video._add_frame(frame)


@pytest.mark.asyncio
async def test_raw_stream_source_decodes_frame(video_server: tuple[BaseVideo, str]) -> None:
    video, url = video_server
    source = make_source(url)
    data = np.arange(12, dtype=np.uint16).reshape(3, 4)
    await video._add_frame(Frame(data, start=time.time(), exposure_time=0.5))

    try:
        image = await asyncio.wait_for(source.next_image(None, 0.0), timeout=5)
    finally:
        await source.close()

    np.testing.assert_array_equal(image.data, data)
    assert image.header["IMAGETYP"] == "guiding"
    assert image.header["VIDFRAME"] == 0
    assert image.header["EXPTIME"] == 0.5
    assert "DTYPE" not in image.header


@pytest.mark.asyncio
async def test_raw_stream_source_skips_frames_started_before_not_before(video_server: tuple[BaseVideo, str]) -> None:
    video, url = video_server
    source = make_source(url)
    not_before = time.time()
    await video._add_frame(Frame(np.zeros((2, 2), dtype=np.uint16), start=not_before - 1.0, exposure_time=0.1))
    feeder = asyncio.create_task(
        add_later(video, [Frame(np.ones((2, 2), dtype=np.uint16), start=not_before + 0.5, exposure_time=0.1)])
    )

    try:
        image = await asyncio.wait_for(source.next_image(None, not_before), timeout=5)
    finally:
        await source.close()
        await feeder

    assert image.header["VIDFRAME"] == 1


@pytest.mark.asyncio
async def test_raw_stream_source_waits_for_requested_exposure_time(video_server: tuple[BaseVideo, str]) -> None:
    video, url = video_server
    source = make_source(url)
    await video._add_frame(Frame(np.zeros((2, 2), dtype=np.uint16), start=time.time(), exposure_time=1.0))
    feeder = asyncio.create_task(
        add_later(video, [Frame(np.ones((2, 2), dtype=np.uint16), start=time.time(), exposure_time=2.0)])
    )

    try:
        image = await asyncio.wait_for(source.next_image(2.0, 0.0), timeout=5)
    finally:
        await source.close()
        await feeder

    assert image.header["EXPTIME"] == 2.0


@pytest.mark.asyncio
async def test_raw_stream_source_crops_around_brightest_star(video_server: tuple[BaseVideo, str]) -> None:
    video, url = video_server
    source = make_source(url, crop_size=20)
    data = star_frame(70, 40)
    await video._add_frame(Frame(data, start=time.time(), exposure_time=0.1))
    feeder = asyncio.create_task(add_later(video, [Frame(data, start=time.time(), exposure_time=0.1)], delay=0.3))

    try:
        image = await asyncio.wait_for(source.next_image(None, 0.0), timeout=10)
    finally:
        await source.close()
        await feeder

    assert image.data.shape == (20, 20)
    assert image.header["CROP-X"] == 60
    assert image.header["CROP-Y"] == 30
    # the star is in the middle of the crop
    y, x = np.unravel_index(np.argmax(image.data), image.data.shape)
    assert abs(x - 10) <= 1 and abs(y - 10) <= 1


@pytest.mark.asyncio
async def test_crop_around_brightest_star_is_clipped_to_image() -> None:
    # SEP ignores sources right at the border, so use a large box to get clipped instead
    crop = await crop_around_brightest_star(star_frame(15, 85), 40)
    assert crop == (0, 60, 40, 40)


@pytest.mark.asyncio
async def test_crop_around_brightest_star_none_without_stars() -> None:
    assert await crop_around_brightest_star(np.full((50, 50), 1000, dtype=np.uint16), 20) is None


def test_accept_estimated_start_gets_one_frame_margin() -> None:
    source = make_source("http://unused")
    t = 1_700_000_000.0
    meta = {"DATE-OBS": Time(t, format="unix").isot, "DATE-SRC": "estimated", "EXPTIME": 1.0}

    assert source._accept(meta, t - 1.0) is True
    assert source._accept(meta, t - 0.5) is False
    assert source._accept({**meta, "DATE-SRC": "device"}, t - 0.5) is True


def test_accept_unknown_start_takes_second_frame_arriving_after_not_before() -> None:
    source = make_source("http://unused")
    t = 1_700_000_000.0
    meta = {"DATE-OBS": Time(t + 1, format="unix").isot, "DATE-ARR": Time(t + 1, format="unix").isot}
    meta["DATE-SRC"] = "unknown"

    # DATE-OBS (= arrival) is after not_before, but the frame may have started before it
    assert source._accept(meta, t, arrived=1) is False
    assert source._accept(meta, t, arrived=2) is True


@pytest.mark.asyncio
async def test_raw_stream_source_unknown_start_skips_frame_in_progress(video_server: tuple[BaseVideo, str]) -> None:
    video, url = video_server
    source = make_source(url)
    not_before = time.time()
    feeder = asyncio.create_task(
        add_later(video, [Frame(np.full((2, 2), i, dtype=np.uint16)) for i in range(2)], delay=0.2)
    )

    try:
        image = await asyncio.wait_for(source.next_image(None, not_before), timeout=5)
    finally:
        await source.close()
        await feeder

    assert image.header["DATE-SRC"] == "unknown"
    assert image.header["VIDFRAME"] == 1


@pytest.mark.asyncio
async def test_raw_stream_source_decodes_colour_frame(video_server: tuple[BaseVideo, str]) -> None:
    video, url = video_server
    source = make_source(url)
    data = np.arange(4 * 5 * 3, dtype=np.uint8).reshape(4, 5, 3)
    await video._add_frame(Frame(data, start=time.time(), exposure_time=0.1))
    feeder = asyncio.create_task(
        add_later(video, [Frame(data + 1, start=time.time() + 1, exposure_time=0.1)], delay=0.2)
    )

    try:
        # two frames in a row: a desynced stream would fail to parse the second one
        first = await asyncio.wait_for(source.next_image(None, 0.0), timeout=5)
        second = await asyncio.wait_for(source.next_image(None, time.time() + 0.5), timeout=5)
    finally:
        await source.close()
        await feeder

    np.testing.assert_array_equal(first.data, data)
    np.testing.assert_array_equal(second.data, data + 1)
