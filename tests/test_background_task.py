from __future__ import annotations

import asyncio
import logging
from unittest.mock import MagicMock

import pytest

from pyobs.background_task import BackgroundTask


def make_task(func, restart=False) -> BackgroundTask:
    parent = MagicMock()
    parent.quit = MagicMock()
    return BackgroundTask(func, restart=restart, parent=parent)


# ── start / stop ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_creates_asyncio_task() -> None:
    ran = asyncio.Event()

    async def func():
        ran.set()

    task = make_task(func, restart=False)
    task.start()
    await asyncio.wait_for(ran.wait(), timeout=1.0)
    task.stop()
    assert task._task is not None


@pytest.mark.asyncio
async def test_stop_cancels_task() -> None:
    started = asyncio.Event()

    async def func():
        started.set()
        await asyncio.sleep(100)

    task = make_task(func, restart=False)
    task.start()
    await asyncio.wait_for(started.wait(), timeout=1.0)
    task.stop()
    await asyncio.sleep(0.05)
    assert task._task.cancelled() or task._task.done()


@pytest.mark.asyncio
async def test_stop_noop_when_not_started() -> None:
    async def func():
        pass

    task = make_task(func)
    task.stop()  # should not raise


# ── normal execution ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_runs_function(caplog) -> None:
    ran = asyncio.Event()

    async def func():
        ran.set()

    task = make_task(func, restart=False)
    task.start()
    await asyncio.wait_for(ran.wait(), timeout=1.0)
    task.stop()


@pytest.mark.asyncio
async def test_no_restart_exits_after_one_run(caplog) -> None:
    call_count = 0

    async def func():
        nonlocal call_count
        call_count += 1

    task = make_task(func, restart=False)
    task.start()
    await asyncio.sleep(0.1)
    task.stop()
    assert call_count == 1


# ── CancelledError ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cancelled_error_exits_cleanly(caplog) -> None:
    async def func():
        raise asyncio.CancelledError()

    task = make_task(func, restart=False)
    with caplog.at_level(logging.INFO):
        task.start()
        await asyncio.sleep(0.1)

    assert "cancelled" in caplog.text.lower()
    assert task._task.done()


# ── exception handling ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_exception_logged(caplog) -> None:
    async def func():
        raise ValueError("something went wrong")

    task = make_task(func, restart=False)
    with caplog.at_level(logging.ERROR):
        task.start()
        await asyncio.sleep(0.1)

    assert "Exception in task" in caplog.text


@pytest.mark.asyncio
async def test_exception_no_restart_quits(caplog) -> None:
    async def func():
        raise ValueError("fail")

    task = make_task(func, restart=False)
    with caplog.at_level(logging.INFO):
        task.start()
        await asyncio.sleep(0.1)

    assert "quitting" in caplog.text
    assert task._task.done()


@pytest.mark.asyncio
async def test_exception_with_restart_continues(caplog) -> None:
    call_count = 0
    done = asyncio.Event()

    async def func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("fail")
        done.set()
        await asyncio.sleep(100)

    task = make_task(func, restart=True)
    with caplog.at_level(logging.INFO):
        task.start()
        await asyncio.wait_for(done.wait(), timeout=2.0)
        task.stop()

    assert call_count >= 3
    assert "restarting" in caplog.text


# ── rapid failure / quit ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rapid_failures_trigger_quit(caplog) -> None:
    """Too many fast failures calls parent.quit() when restart=True."""

    async def func():
        raise ValueError("fast fail")

    parent = MagicMock()
    task = BackgroundTask(func, restart=True, parent=parent)

    with caplog.at_level(logging.ERROR):
        task.start()
        await asyncio.sleep(0.5)

    parent.quit.assert_called_once()
    assert "too fast" in caplog.text


@pytest.mark.asyncio
async def test_rapid_failures_no_restart_just_quits(caplog) -> None:
    """Too many fast failures with restart=False just stops without calling quit."""

    async def func():
        raise ValueError("fast fail")

    parent = MagicMock()
    task = BackgroundTask(func, restart=False, parent=parent)

    with caplog.at_level(logging.ERROR):
        task.start()
        await asyncio.sleep(0.5)

    parent.quit.assert_not_called()
    assert task._task.done()


@pytest.mark.asyncio
async def test_slow_failures_reset_counter(caplog) -> None:
    """Failures spread over time don't trigger the rapid-failure quit."""
    call_count = 0
    done = asyncio.Event()

    async def func():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise ValueError("slow fail")
        done.set()
        await asyncio.sleep(100)

    parent = MagicMock()
    # Patch MAX_FINISH_INTERVAL_SECONDS to make the test think enough time passed
    import pyobs.background_task as bt_module

    original = bt_module.MAX_FINISH_INTERVAL_SECONDS
    bt_module.MAX_FINISH_INTERVAL_SECONDS = 0  # any gap resets the counter

    task = BackgroundTask(func, restart=True, parent=parent)
    task.start()
    await asyncio.wait_for(done.wait(), timeout=2.0)
    task.stop()

    bt_module.MAX_FINISH_INTERVAL_SECONDS = original
    parent.quit.assert_not_called()
