import asyncio
import os
import threading
import time
from pathlib import Path

import pytest

import pyobs.vfs.localfile as localfile_module
from pyobs.vfs import LocalFile

"""
@pytest.mark.asyncio
async def test_read_file() -> None:
    # create config
    root = os.path.dirname(__file__)

    # open file
    filename = os.path.basename(__file__)
    async with LocalFile(filename, "r", root=root) as f:
        assert f.readline() == b"import os" + bytes(os.linesep, "utf-8")
"""


@pytest.mark.asyncio
async def test_file_not_found() -> None:
    # create config
    root = os.path.dirname(__file__)

    # open file
    with pytest.raises(FileNotFoundError):
        async with LocalFile("doesnt_exist.txt", "r", root=root):
            pass


@pytest.mark.asyncio
async def test_invalid_path() -> None:
    # create config
    root = os.path.dirname(__file__)

    # open file
    with pytest.raises(ValueError):
        async with LocalFile("../test.txt", "r", root=root):
            pass

    # open file
    with pytest.raises(ValueError):
        async with LocalFile("/test.txt", "r", root=root):
            pass


@pytest.mark.asyncio
async def test_write_file(tmp_path: Path) -> None:
    # create config
    root = str(tmp_path)

    # open file for write
    async with LocalFile("test.txt", "w", root=root) as f:
        await f.write("This is a test")

    # test it
    assert tmp_path.joinpath("test.txt").read_text() == "This is a test"


@pytest.mark.asyncio
async def test_create_dir(tmp_path: Path) -> None:
    # create config
    root = str(tmp_path)

    # open file for write
    async with LocalFile("sub/test.txt", "w", root=root) as f:
        await f.write("This is a test")

    # test it
    assert tmp_path.joinpath("sub/test.txt").read_text() == "This is a test"

    # this should throw an exception
    with pytest.raises(ValueError):
        async with LocalFile("sub2/test.txt", "w", root=root, mkdir=False) as f:
            await f.write("This is a test")


# ── event-loop responsiveness ────────────────────────────────────────────────


class SlowFd:
    """Fake file object whose I/O blocks for a fixed time, simulating slow local disk access."""

    def __init__(self, delay: float = 0.2):
        self._delay = delay

    def read(self, n: int = -1) -> bytes:
        time.sleep(self._delay)
        return b"data"

    def write(self, s: str | bytes) -> None:
        time.sleep(self._delay)

    def close(self) -> None:
        pass


async def _run_with_heartbeat(coro, interval: float = 0.01):
    """Runs coro concurrently with a fast heartbeat, returns (coro's result, heartbeat count)."""
    stop = asyncio.Event()
    heartbeats = 0

    async def heartbeat() -> None:
        nonlocal heartbeats
        while not stop.is_set():
            await asyncio.sleep(interval)
            heartbeats += 1

    async def run_and_stop():
        result = await coro
        stop.set()
        return result

    result, _ = await asyncio.gather(run_and_stop(), heartbeat())
    return result, heartbeats


@pytest.mark.asyncio
async def test_read_does_not_block_event_loop(tmp_path: Path) -> None:
    """A slow read must not freeze the loop: offloaded, a heartbeat keeps ticking."""
    async with LocalFile("test.txt", "w", root=str(tmp_path)) as f:
        f.fd.close()
        f.fd = SlowFd()
        data, heartbeats = await _run_with_heartbeat(f.read())

    assert data == b"data"
    assert heartbeats >= 5


@pytest.mark.asyncio
async def test_write_does_not_block_event_loop(tmp_path: Path) -> None:
    """A slow write must not freeze the loop: offloaded, a heartbeat keeps ticking."""
    async with LocalFile("test.txt", "w", root=str(tmp_path)) as f:
        f.fd.close()
        f.fd = SlowFd()
        _, heartbeats = await _run_with_heartbeat(f.write("x"))

    assert heartbeats >= 5


@pytest.mark.asyncio
async def test_async_enter_does_not_block_event_loop(monkeypatch, tmp_path: Path) -> None:
    """A slow open (e.g. a network-mounted watch path) must not freeze the loop."""

    # simulate a slow file open
    def slow_open(full_path: str, mode: str, mkdir: bool):
        time.sleep(0.2)
        return open(full_path, mode)

    monkeypatch.setattr(localfile_module, "_open_sync", slow_open)

    async def open_write_close():
        async with LocalFile("test.txt", "w", root=str(tmp_path)) as f:
            await f.write("This is a test")

    _, heartbeats = await _run_with_heartbeat(open_write_close())

    assert heartbeats >= 5
    assert tmp_path.joinpath("test.txt").read_text() == "This is a test"


@pytest.mark.asyncio
async def test_concurrent_opens_creating_same_new_dir(monkeypatch, tmp_path: Path) -> None:
    """Concurrent opens racing to create the same not-yet-existing sub-directory must not raise.

    __aenter__ moved directory creation onto executor threads, so the exists()/makedirs()
    check-then-act in _open_sync races for real between threads. A barrier deterministically
    forces every thread past the exists() check before any calls makedirs(), guaranteeing the
    race window is hit; regression test for the resulting FileExistsError.
    """
    root = str(tmp_path)
    n = 4
    target_dir = os.path.join(root, "newdir")
    barrier = threading.Barrier(n)
    real_exists = os.path.exists

    def widened_exists(path: str) -> bool:
        result = real_exists(path)
        # only synchronize on the exists() checks we're racing; ignore unrelated calls made
        # concurrently elsewhere in the process (e.g. by asyncio/pytest internals)
        if not result and path == target_dir:
            barrier.wait(timeout=5)
        return result

    monkeypatch.setattr(os.path, "exists", widened_exists)

    async def open_write_close(i: int) -> None:
        async with LocalFile(f"newdir/file{i}.txt", "w", root=root) as f:
            await f.write("data")

    await asyncio.gather(*(open_write_close(i) for i in range(n)))

    for i in range(n):
        assert tmp_path.joinpath("newdir", f"file{i}.txt").read_text() == "data"
