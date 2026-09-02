from __future__ import annotations

import asyncio
import io
import logging
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from astropy.io import fits

from pyobs.comm.dummy import DummyComm
from pyobs.modules.image import imagewatcher as imagewatcher_module
from pyobs.modules.image.imagewatcher import ImageWatcher
from pyobs.vfs import VirtualFileSystem


def make_watcher(
    destinations=None, pattern="*", wait_time=0, flatten=True, poll=False, poll_interval=5
) -> ImageWatcher:
    return ImageWatcher(
        watchpath="/watch",
        destinations=destinations or ["/dest"],
        pattern=pattern,
        wait_time=wait_time,
        flatten=flatten,
        poll=poll,
        poll_interval=poll_interval,
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


# ── FITS-parse gating by filename suffix ──────────────────────────────────────


@pytest.mark.parametrize("name", ["frame.0", "frame.txt", "frame.bin", "frame"])
@pytest.mark.asyncio
async def test_worker_does_not_parse_non_fits_filenames(monkeypatch, name) -> None:
    """A file whose name doesn't look like FITS is still copied as-is to a non-templated
    destination, but is never handed to astropy -- no parse attempt, so no astropy header
    warnings for e.g. raw camera binaries ("frame.0" here, per a real incident)."""
    watcher = make_watcher(destinations=["/dest"], wait_time=0)
    data = b"\x00\x01\x02 raw binary, definitely not fits"
    read_ctx, write_ctx = make_read_write_ctx(data)

    def open_side_effect(filename, mode):
        return read_ctx if mode == "rb" else write_ctx

    watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)
    watcher._vfs.remove = AsyncMock(return_value=True)

    parse_calls = []

    def unexpected_fromstring(_data: bytes):
        parse_calls.append(_data)
        return None

    monkeypatch.setattr(imagewatcher_module.fits.HDUList, "fromstring", staticmethod(unexpected_fromstring))

    watcher._queue.put_nowait((f"/watch/{name}", 0.0))
    task = asyncio.create_task(watcher._worker())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    assert parse_calls == []
    assert watcher.current_file is not None
    assert watcher.current_file.hdu_list is None
    watcher._vfs.remove.assert_called_once_with(f"/watch/{name}")


@pytest.mark.parametrize("name", ["frame.fits", "frame.fitz", "frame.fits.gz", "frame.fits.fz", "FRAME.FITS"])
@pytest.mark.asyncio
async def test_worker_parses_fits_filename_suffixes(monkeypatch, name) -> None:
    """Files whose names match the FITS suffixes still get the (best-effort) parse attempt."""
    watcher = make_watcher(destinations=["/dest"], wait_time=0)
    data = b"some data"
    read_ctx, write_ctx = make_read_write_ctx(data)

    def open_side_effect(filename, mode):
        return read_ctx if mode == "rb" else write_ctx

    watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)
    watcher._vfs.remove = AsyncMock(return_value=True)

    parse_calls = []

    def recording_fromstring(parsed: bytes):
        parse_calls.append(parsed)
        return MagicMock()

    monkeypatch.setattr(imagewatcher_module.fits.HDUList, "fromstring", staticmethod(recording_fromstring))

    watcher._queue.put_nowait((f"/watch/{name}", 0.0))
    task = asyncio.create_task(watcher._worker())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    assert parse_calls == [data]
    assert watcher.current_file is not None
    watcher._vfs.remove.assert_called_once_with(f"/watch/{name}")


@pytest.mark.asyncio
async def test_worker_parse_failure_on_fits_name_still_copies_file() -> None:
    """A .fits-named file whose bytes fail to parse (corrupt/truncated) is still copied as-is
    to a non-templated destination -- the parse is best-effort, not a gate on copying."""
    watcher = make_watcher(destinations=["/dest"], wait_time=0)
    data = b"not really fits but named like it"
    read_ctx, write_ctx = make_read_write_ctx(data)

    def open_side_effect(filename, mode):
        return read_ctx if mode == "rb" else write_ctx

    watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)
    watcher._vfs.remove = AsyncMock(return_value=True)

    watcher._queue.put_nowait(("/watch/corrupt.fits", 0.0))
    task = asyncio.create_task(watcher._worker())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    assert watcher.current_file is not None
    assert watcher.current_file.hdu_list is None
    watcher._vfs.remove.assert_called_once_with("/watch/corrupt.fits")


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


# ── flatten ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_worker_flattens_nested_path_by_default() -> None:
    """flatten=True (default): a file found in a subdirectory still lands at the destination
    root, keyed only by its basename -- the pre-existing, non-recursive behavior."""
    watcher = make_watcher(destinations=["/dest"], wait_time=0, flatten=True)
    data = b"raw data"
    read_ctx, write_ctx = make_read_write_ctx(data)

    def open_side_effect(filename, mode):
        return read_ctx if mode == "rb" else write_ctx

    watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)
    watcher._vfs.remove = AsyncMock(return_value=True)

    watcher._queue.put_nowait(("/watch/2026/09/02/test.fits", 0.0))
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
async def test_worker_preserves_relative_path_when_not_flattened() -> None:
    """flatten=False: a file found in a subdirectory keeps that subdirectory structure under
    the destination."""
    watcher = make_watcher(destinations=["/dest"], wait_time=0, flatten=False)
    data = b"raw data"
    read_ctx, write_ctx = make_read_write_ctx(data)

    def open_side_effect(filename, mode):
        return read_ctx if mode == "rb" else write_ctx

    watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)
    watcher._vfs.remove = AsyncMock(return_value=True)

    watcher._queue.put_nowait(("/watch/2026/09/02/test.fits", 0.0))
    task = asyncio.create_task(watcher._worker())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    assert watcher.current_file is not None
    assert watcher.current_file.out_filename == "/dest/2026/09/02/test.fits"


@pytest.mark.asyncio
async def test_worker_flatten_false_still_uses_fits_header_template() -> None:
    """flatten only governs the non-templated branch -- a {placeholder} destination pattern
    is unaffected either way."""
    watcher = make_watcher(destinations=["/dest/{FNAME}"], wait_time=0, flatten=False)
    data = make_fits_bytes()
    read_ctx, write_ctx = make_read_write_ctx(data)

    def open_side_effect(filename, mode):
        return read_ctx if mode == "rb" else write_ctx

    watcher._vfs.open_file = MagicMock(side_effect=open_side_effect)
    watcher._vfs.remove = AsyncMock(return_value=True)

    watcher._queue.put_nowait(("/watch/2026/09/02/img.fits", 0.0))
    task = asyncio.create_task(watcher._worker())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    assert watcher.current_file is not None
    assert watcher.current_file.out_filename == "/dest/test.fits"


# ── recursive polling / initial scan ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_watch_poll_picks_up_nested_files() -> None:
    watcher = make_watcher(poll=True, poll_interval=0)
    # side_effect list: first call is the initial scan (empty), every call after returns the
    # nested file -- avoids relying on list exhaustion to end the test (that would raise
    # StopAsyncIteration inside the task instead of the explicit cancel below doing it).
    watcher._vfs.find = AsyncMock(
        side_effect=lambda *a, **kw: [] if watcher._vfs.find.call_count == 1 else ["2026/09/02/test.fits"]
    )

    added: list[str] = []

    async def fake_add_file(filename: str) -> None:
        added.append(filename)

    watcher.add_file = fake_add_file

    task = asyncio.create_task(watcher._watch_poll())
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    assert added == ["/watch/2026/09/02/test.fits"]
    # pattern filtering happens in add_file, not here: find() is always called unfiltered
    watcher._vfs.find.assert_called_with("/watch", "*")


@pytest.mark.asyncio
async def test_watch_poll_and_inotify_apply_pattern_consistently() -> None:
    """Regression for a review finding: poll mode used to pre-filter find() by pattern (matched
    per-directory against each entry's basename), while inotify mode only ever filtered in
    add_file (matched against the full path) -- a real behavioral divergence for a pattern like
    "*2026*" against a file under a "2026/" subdirectory. Both now defer entirely to add_file, so
    this exercises the real (unmocked) add_file to prove the filtering actually happens there."""
    watcher = make_watcher(poll=True, poll_interval=0, pattern="*.fits")
    found = ["2026/keep.fits", "2026/skip.txt"]
    # first call (the initial baseline scan) sees nothing yet, so the files "found" afterward
    # register as new and get queued
    watcher._vfs.find = AsyncMock(side_effect=lambda *a, **kw: [] if watcher._vfs.find.call_count == 1 else found)

    task = asyncio.create_task(watcher._watch_poll())
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    # find() itself is unfiltered ("*"); only the .fits file survives add_file's own check
    watcher._vfs.find.assert_called_with("/watch", "*")
    queued = []
    while not watcher._queue.empty():
        filename, _ = watcher._queue.get_nowait()
        queued.append(filename)
    assert queued == ["/watch/2026/keep.fits"]


@pytest.mark.asyncio
async def test_watch_poll_respects_poll_interval() -> None:
    """Regression: the pre-existing implementation never awaited poll_interval at all, so it
    busy-looped. Confirm the sleep is actually observed between iterations."""
    watcher = make_watcher(poll=True, poll_interval=123)
    watcher._vfs.find = AsyncMock(return_value=[])

    sleep_calls: list[float] = []
    real_sleep = asyncio.sleep

    async def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)
        if len(sleep_calls) >= 2:
            raise asyncio.CancelledError
        await real_sleep(0)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(imagewatcher_module.asyncio, "sleep", fake_sleep)
        task = asyncio.create_task(watcher._watch_poll())
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass

    assert sleep_calls[:2] == [123, 123]


@pytest.mark.asyncio
async def test_open_scans_nested_files() -> None:
    watcher = make_watcher()
    watcher._vfs.find = AsyncMock(return_value=["2026/09/02/test.fits"])

    added: list[str] = []

    async def fake_add_file(filename: str) -> None:
        added.append(filename)

    watcher.add_file = fake_add_file

    await watcher.open()

    assert added == ["/watch/2026/09/02/test.fits"]
    watcher._vfs.find.assert_called_once_with("/watch", "*")


# ── recursive inotify watching (real filesystem) ────────────────────────────────


@pytest.mark.asyncio
async def test_watch_inotify_picks_up_file_in_new_nested_subdirectory(tmp_path: Path) -> None:
    """A directory created after the watcher starts, containing a file, is still picked up --
    covering the CREATE-then-write-into-it pattern (e.g. an observation's per-run directory)."""
    watcher = make_watcher()
    watcher._vfs.local_path = AsyncMock(return_value=str(tmp_path))

    added: list[str] = []

    async def fake_add_file(filename: str) -> None:
        added.append(filename)

    watcher.add_file = fake_add_file

    task = asyncio.create_task(watcher._watch_inotify())
    await asyncio.sleep(0.1)

    sub = tmp_path / "2026" / "09" / "02"
    sub.mkdir(parents=True)
    await asyncio.sleep(0.1)
    (sub / "test.fits").write_bytes(b"data")

    await asyncio.sleep(0.3)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    assert added == ["/watch/2026/09/02/test.fits"]


@pytest.mark.asyncio
async def test_watch_inotify_survives_delete_and_recreate_of_watched_directory(tmp_path: Path) -> None:
    """The watched root's subdirectory being deleted and recreated (e.g. pyftscontrol's
    create_observation_directory, which rmtree()s and re-mkdir()s the same "tmp" scratch dir
    before every run) must not silently stop future files in it from being detected."""
    watcher = make_watcher()
    watcher._vfs.local_path = AsyncMock(return_value=str(tmp_path))

    added: list[str] = []

    async def fake_add_file(filename: str) -> None:
        added.append(filename)

    watcher.add_file = fake_add_file

    task = asyncio.create_task(watcher._watch_inotify())
    await asyncio.sleep(0.1)

    scratch = tmp_path / "tmp"
    scratch.mkdir()
    await asyncio.sleep(0.1)
    (scratch / "first.fits").write_bytes(b"data")
    await asyncio.sleep(0.1)

    # delete and recreate the same directory, as pyftscontrol does before every observation
    (scratch / "first.fits").unlink()
    scratch.rmdir()
    await asyncio.sleep(0.1)
    scratch.mkdir()
    await asyncio.sleep(0.1)
    (scratch / "second.fits").write_bytes(b"data")

    await asyncio.sleep(0.3)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    assert "/watch/tmp/first.fits" in added
    assert "/watch/tmp/second.fits" in added


@pytest.mark.asyncio
async def test_watch_inotify_survives_rename_into_watched_tree(tmp_path: Path) -> None:
    """A directory renamed (moved) into its final location within the watched tree -- as
    pyftscontrol's move_observation_directory does -- must still be watched afterward, including
    files written into it after the rename."""
    # both the scratch dir and the destination's parent tree exist before the watcher starts,
    # so they're covered by the initial recursive watch -- isolates the rename/MOVED_FROM+
    # MOVED_TO handling from the (separately covered) CREATE-triggered sub-watch timing.
    scratch = tmp_path / "tmp"
    scratch.mkdir()
    final_dir = tmp_path / "2026" / "09" / "02"
    final_dir.parent.mkdir(parents=True)

    watcher = make_watcher()
    watcher._vfs.local_path = AsyncMock(return_value=str(tmp_path))

    added: list[str] = []

    async def fake_add_file(filename: str) -> None:
        added.append(filename)

    watcher.add_file = fake_add_file

    task = asyncio.create_task(watcher._watch_inotify())
    await asyncio.sleep(0.1)

    scratch.rename(final_dir)
    await asyncio.sleep(0.1)

    # written after the rename, at the new (final) location
    (final_dir / "result.fits").write_bytes(b"data")

    await asyncio.sleep(0.3)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    assert added == ["/watch/2026/09/02/result.fits"]


@pytest.mark.asyncio
async def test_watch_inotify_restarts_on_oserror(monkeypatch) -> None:
    """Regression for a review finding: asyncinotify's own add_watch/rm_watch (inside
    watch_recursive()) can raise OSError if a directory vanishes between an event being received
    and the library acting on it -- real under directory churn, not hypothetical. Confirm
    _watch_inotify catches it and restarts with a fresh RecursiveWatcher instead of letting the
    whole background task die."""
    watcher = make_watcher()
    watcher._vfs.local_path = AsyncMock(return_value="/some/local/path")

    added: list[str] = []

    async def fake_add_file(filename: str) -> None:
        added.append(filename)

    watcher.add_file = fake_add_file

    class FakeEvent:
        def __init__(self, path: Path) -> None:
            self.path = path

    attempts = 0

    class FakeRecursiveWatcher:
        def __init__(self, path: Path, mask: object) -> None:
            nonlocal attempts
            attempts += 1
            self._attempt = attempts

        async def watch_recursive(self):
            if self._attempt == 1:
                # simulate a directory vanishing mid-scan, as asyncinotify's own bookkeeping would
                raise OSError("directory vanished mid-scan")
            yield FakeEvent(Path("/some/local/path/test.fits"))
            await asyncio.sleep(3600)  # stay "alive" until the test cancels it

    monkeypatch.setattr("asyncinotify.RecursiveWatcher", FakeRecursiveWatcher)

    task = asyncio.create_task(watcher._watch_inotify())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    assert attempts == 2, "expected a fresh RecursiveWatcher after the first one's OSError"
    assert added == ["/watch/test.fits"]


@pytest.mark.xfail(strict=True, reason="known asyncinotify/kernel-level race, see docstring")
@pytest.mark.asyncio
async def test_watch_inotify_loses_race_on_rename_into_freshly_created_deep_dir(tmp_path: Path) -> None:
    """Known gap, not a bug we can fix here: when a *destination* directory tree that doesn't
    exist yet is created and something is renamed into it before this process's asyncio loop
    gets scheduled to consume the resulting CREATE event(s) and add a watch, the move is never
    seen -- inotify only reports events for already-watched parents, and nothing later
    re-discovers the miss. Reproduced directly against asyncinotify.RecursiveWatcher outside
    pytest too, so this is a genuine kernel/library-level race, not a mock or test artifact; the
    upstream example script (asyncinotify's examples/recursivewatch.py) documents the same
    caveat ("doing two changes on a directory before the program has a time to handle it").

    Practical exposure for a consumer building on this: only the *first* write into a brand-new
    multi-level destination directory (e.g. a new {year}/{month} not yet on disk) is at risk --
    every subsequent one that day is a no-op mkdir, no CREATE event, no race. Mitigation belongs
    at the consumer/deployment level (e.g. a periodic reconciliation re-scan, the standard fix for
    inotify-based systems), not in ImageWatcher itself.
    """
    watcher = make_watcher()
    watcher._vfs.local_path = AsyncMock(return_value=str(tmp_path))

    added: list[str] = []

    async def fake_add_file(filename: str) -> None:
        added.append(filename)

    watcher.add_file = fake_add_file

    task = asyncio.create_task(watcher._watch_inotify())
    await asyncio.sleep(0.1)

    scratch = tmp_path / "tmp"
    scratch.mkdir()
    await asyncio.sleep(0.1)

    # created and renamed-into with no yield in between: the watcher process has no chance to
    # consume the CREATE event(s) for the new tree before the rename fires.
    final_dir = tmp_path / "2026" / "09" / "02"
    final_dir.parent.mkdir(parents=True)
    scratch.rename(final_dir)
    await asyncio.sleep(0.1)

    (final_dir / "result.fits").write_bytes(b"data")

    await asyncio.sleep(0.3)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass

    assert added == ["/watch/2026/09/02/result.fits"]
