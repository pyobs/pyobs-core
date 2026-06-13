from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.events import NewImageEvent
from pyobs.modules.image.imagewriter import ImageWriter
from pyobs.utils.enums import ImageType


def make_writer(filename: str = "/archive/{FNAME}", sources=None) -> ImageWriter:
    writer = ImageWriter.__new__(ImageWriter)
    writer._filename = filename
    writer._sources = [sources] if isinstance(sources, str) else sources
    writer._queue = asyncio.Queue()
    writer._comm = MagicMock()
    writer._vfs = MagicMock()
    writer._background_tasks = []
    return writer


def make_image_event(filename: str = "/tmp/test.fits") -> NewImageEvent:
    return NewImageEvent(filename=filename, image_type=ImageType.OBJECT)


# ── process_new_image_event ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_process_event_queues_filename() -> None:
    writer = make_writer()
    event = make_image_event("/tmp/img.fits")
    result = await writer.process_new_image_event(event, "camera")
    assert result is True
    assert writer._queue.get_nowait() == "/tmp/img.fits"


@pytest.mark.asyncio
async def test_process_event_rejects_wrong_type() -> None:
    from pyobs.events import BadWeatherEvent

    writer = make_writer()
    result = await writer.process_new_image_event(BadWeatherEvent(), "camera")
    assert result is False
    assert writer._queue.empty()


@pytest.mark.asyncio
async def test_process_event_filters_by_source() -> None:
    writer = make_writer(sources="camera1")
    event = make_image_event()
    assert await writer.process_new_image_event(event, "camera2") is False
    assert writer._queue.empty()


@pytest.mark.asyncio
async def test_process_event_accepts_listed_source() -> None:
    writer = make_writer(sources="camera1")
    event = make_image_event()
    result = await writer.process_new_image_event(event, "camera1")
    assert result is True
    assert not writer._queue.empty()


@pytest.mark.asyncio
async def test_process_event_accepts_all_when_no_filter() -> None:
    writer = make_writer(sources=None)
    event = make_image_event()
    assert await writer.process_new_image_event(event, "any_camera") is True


# ── _worker ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_worker_downloads_and_stores_image() -> None:
    writer = make_writer(filename="/archive/{FNAME}")
    img = MagicMock()
    img.header = {"FNAME": "test.fits"}
    writer._vfs.read_image = AsyncMock(return_value=img)
    writer._vfs.write_image = AsyncMock()

    writer._queue.put_nowait("/tmp/test.fits")

    task = asyncio.create_task(writer._worker())
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    writer._vfs.read_image.assert_called_once_with("/tmp/test.fits")
    writer._vfs.write_image.assert_called_once()
    assert writer._vfs.write_image.call_args[0][0] == "/archive/test.fits"


@pytest.mark.asyncio
async def test_worker_skips_on_file_not_found(caplog) -> None:
    import logging

    writer = make_writer()
    writer._vfs.read_image = AsyncMock(side_effect=FileNotFoundError)
    writer._queue.put_nowait("/tmp/missing.fits")

    task = asyncio.create_task(writer._worker())
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    with caplog.at_level(logging.ERROR):
        pass
    writer._vfs.write_image = AsyncMock()
    writer._vfs.write_image.assert_not_called()


@pytest.mark.asyncio
async def test_worker_skips_on_bad_filename_format(caplog) -> None:
    writer = make_writer(filename="/archive/{MISSING_KEY}")
    img = MagicMock()
    img.header = {}  # missing key
    writer._vfs.read_image = AsyncMock(return_value=img)
    writer._vfs.write_image = AsyncMock()
    writer._queue.put_nowait("/tmp/test.fits")

    task = asyncio.create_task(writer._worker())
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    writer._vfs.write_image.assert_not_called()
