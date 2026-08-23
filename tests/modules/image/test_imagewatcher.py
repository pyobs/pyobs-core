from __future__ import annotations

import asyncio
import io
import logging
import time
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from astropy.io import fits

from pyobs.comm.dummy import DummyComm
from pyobs.modules.image import imagewatcher as imagewatcher_module
from pyobs.modules.image.imagewatcher import ImageWatcher
from pyobs.vfs import VirtualFileSystem


def make_watcher(destinations=None, pattern="*", wait_time=0) -> ImageWatcher:
    return ImageWatcher(
        watchpath="/watch",
        destinations=destinations or ["/dest"],
        pattern=pattern,
        wait_time=wait_time,
        comm=DummyComm(),
        vfs=MagicMock(spec=VirtualFileSystem),
    )


def make_fits_bytes() -> bytes:
    primary = fits.PrimaryHDU()
    sci = fits.ImageHDU(np.zeros((10, 10)), name="SCI")
    sci.header["FNAME"] = "test.fits"
    hdul = fits.HDUList([primary, sci])
    buf = io.BytesIO()
    hdul.writeto(buf)
    return buf.getvalue()


def make_read_write_ctx(data: bytes) -> tuple[MagicMock, MagicMock]:
    read_ctx = MagicMock()
    read_ctx.__aenter__ = AsyncMock(return_value=MagicMock(read=AsyncMock(return_value=data)))
    read_ctx.__aexit__ = AsyncMock(return_value=False)

    write_ctx = MagicMock()
    write_ctx.__aenter__ = AsyncMock(return_value=MagicMock(write=AsyncMock()))
    write_ctx.__aexit__ = AsyncMock(return_value=False)

    return read_ctx, write_ctx


# ── add_file ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_file_queues_filename() -> None:
    watcher = make_watcher()
    await watcher.add_file("/watch/test.fits")
    assert not watcher._queue.empty()
    filename, _ = watcher._queue.get_nowait()
    assert filename == "/watch/test.fits"


@pytest.mark.asyncio
async def test_add_file_stores_ready_at_time() -> None:
    watcher = make_watcher(wait_time=5)
    before = time.time()
    await watcher.add_file("/watch/test.fits")
    _, ready_at = watcher._queue.get_nowait()
    assert isinstance(ready_at, float)
    assert ready_at >= before + 5.0


@pytest.mark.asyncio
async def test_add_file_respects_pattern() -> None:
    watcher = make_watcher(pattern="*.fits")
    await watcher.add_file("/watch/test.fits")
    assert not watcher._queue.empty()


@pytest.mark.asyncio
async def test_add_file_skips_non_matching_pattern() -> None:
    watcher = make_watcher(pattern="*.fits")
    await watcher.add_file("/watch/test.txt")
    assert watcher._queue.empty()


# ── _worker ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_worker_copies_file_to_destination() -> None:
    watcher = make_watcher(destinations=["/dest"], wait_time=0)
    data = b"raw data"
    read_ctx, write_ctx = make_read_write_ctx(data)

    def open_side_effect(filename, mode):
        return read_ctx if mode == "rb" else write_ctx

    watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)
    watcher._vfs.remove = AsyncMock(return_value=True)

    watcher._queue.put_nowait(("/watch/test.fits", 0.0))
    task = asyncio.create_task(watcher._worker())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    assert watcher.current_file is not None
    assert watcher.current_file.filename == "/watch/test.fits"


@pytest.mark.asyncio
async def test_worker_deletes_file_after_success() -> None:
    watcher = make_watcher(destinations=["/dest"], wait_time=0)
    data = b"raw data"
    read_ctx, write_ctx = make_read_write_ctx(data)

    def open_side_effect(filename, mode):
        return read_ctx if mode == "rb" else write_ctx

    watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)
    watcher._vfs.remove = AsyncMock(return_value=True)

    watcher._queue.put_nowait(("/watch/test.fits", 0.0))
    task = asyncio.create_task(watcher._worker())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    watcher._vfs.remove.assert_called_once_with("/watch/test.fits")


@pytest.mark.asyncio
async def test_worker_formats_fits_filename() -> None:
    watcher = make_watcher(destinations=["/dest/{FNAME}"], wait_time=0)
    data = make_fits_bytes()
    read_ctx, write_ctx = make_read_write_ctx(data)

    def open_side_effect(filename, mode):
        return read_ctx if mode == "rb" else write_ctx

    watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)
    watcher._vfs.remove = AsyncMock(return_value=True)

    watcher._queue.put_nowait(("/watch/img.fits", 0.0))
    task = asyncio.create_task(watcher._worker())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    assert watcher.current_file is not None
    assert watcher.current_file.out_filename == "/dest/test.fits"


@pytest.mark.asyncio
async def test_worker_requeues_on_write_failure(caplog) -> None:
    """On write failure the file is re-queued and remove is NOT called."""
    watcher = make_watcher(destinations=["/dest"], wait_time=100)
    data = b"raw data"

    read_ctx = MagicMock()
    read_ctx.__aenter__ = AsyncMock(return_value=MagicMock(read=AsyncMock(return_value=data)))
    read_ctx.__aexit__ = AsyncMock(return_value=False)

    write_ctx = MagicMock()
    write_ctx.__aenter__ = AsyncMock(side_effect=OSError("write failed"))
    write_ctx.__aexit__ = AsyncMock(return_value=False)

    def open_side_effect(filename, mode):
        return read_ctx if mode == "rb" else write_ctx

    watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)
    watcher._vfs.remove = AsyncMock(return_value=True)

    watcher._queue.put_nowait(("/watch/test.fits", 0.0))

    with caplog.at_level(logging.WARNING):
        task = asyncio.create_task(watcher._worker())
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass

    watcher._vfs.remove.assert_not_called()
    assert "skipping for now" in caplog.text


# ── event-loop responsiveness during file processing ─────────────────────────


@pytest.mark.asyncio
async def test_worker_fits_parse_does_not_block_event_loop(monkeypatch) -> None:
    """A slow FITS parse must not freeze the loop: offloaded, a heartbeat keeps ticking."""
    watcher = make_watcher(destinations=["/dest"], wait_time=0)
    data = b"raw data"
    read_ctx, write_ctx = make_read_write_ctx(data)

    def open_side_effect(filename, mode):
        return read_ctx if mode == "rb" else write_ctx

    watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)

    # the file is fully processed once remove (the last step) is reached
    removed = asyncio.Event()
    watcher._vfs.remove = AsyncMock(side_effect=lambda path: removed.set())

    # simulate a slow, CPU-heavy FITS parse
    def slow_fromstring(_data: bytes):
        time.sleep(0.2)
        return None

    monkeypatch.setattr(imagewatcher_module.fits.HDUList, "fromstring", staticmethod(slow_fromstring))

    watcher._queue.put_nowait(("/watch/test.fits", 0.0))
    worker = asyncio.create_task(watcher._worker())

    heartbeats = 0

    async def heartbeat() -> None:
        nonlocal heartbeats
        while not removed.is_set():
            await asyncio.sleep(0.01)
            heartbeats += 1

    try:
        await asyncio.wait_for(heartbeat(), timeout=5)
    finally:
        worker.cancel()
        try:
            await worker
        except (asyncio.CancelledError, Exception):
            pass

    # ~0.2s of parse at a 10ms heartbeat cadence: the loop should have kept ticking throughout
    # if (and only if) the parse was actually offloaded onto a worker thread.
    assert heartbeats >= 5


# ── process_extra / cleanup_extra ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_process_extra_returns_true() -> None:
    watcher = make_watcher()
    assert await watcher.process_extra("/watch/test.fits") is True


@pytest.mark.asyncio
async def test_cleanup_extra_is_noop() -> None:
    watcher = make_watcher()
    await watcher.cleanup_extra("/watch/test.fits")


# ── constructor ───────────────────────────────────────────────────────────────


def test_constructor_raises_without_destinations() -> None:
    with pytest.raises(ValueError, match="No filename patterns"):
        ImageWatcher(watchpath="/watch", destinations=[])
