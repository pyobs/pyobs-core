from __future__ import annotations

import asyncio

import pytest

from pyobs.utils.parallel import Future

# ── basic functionality ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_future_resolves_immediately() -> None:
    """Future(empty=True) is already done and returns None."""
    f = Future(empty=True)
    assert f.done()
    result = await f
    assert result is None


@pytest.mark.asyncio
async def test_future_returns_result() -> None:
    """Future resolves with the value set on it."""
    f = Future()
    asyncio.get_running_loop().call_soon(f.set_result, 42)
    result = await f
    assert result == 42


@pytest.mark.asyncio
async def test_future_raises_exception() -> None:
    """Future propagates exceptions set on it."""
    f = Future()
    asyncio.get_running_loop().call_soon(f.set_exception, ValueError("oops"))
    with pytest.raises(ValueError, match="oops"):
        await f


# ── timeout ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_default_timeout_raises_after_10s(monkeypatch) -> None:
    """Future with no @timeout raises TimeoutError after 10 seconds."""
    f = Future()
    assert f.timeout is None

    # accelerate: make call_later fire immediately for timeout=10.0
    loop = asyncio.get_running_loop()
    original_call_later = loop.call_later

    def fast_call_later(delay, callback, *args):
        # fire instantly for the 10s default timeout
        if delay == 10.0:
            return original_call_later(0, callback, *args)
        return original_call_later(delay, callback, *args)

    monkeypatch.setattr(loop, "call_later", fast_call_later)

    with pytest.raises(TimeoutError):
        await f


@pytest.mark.asyncio
async def test_set_timeout_extends_wait(monkeypatch) -> None:
    """Future with set_timeout uses that value instead of 10s."""
    f = Future()
    f.set_timeout(30.0)
    assert f.get_timeout() == 30.0

    loop = asyncio.get_running_loop()
    original_call_later = loop.call_later
    fired_delays = []

    def recording_call_later(delay, callback, *args):
        fired_delays.append(delay)
        if delay == 30.0:
            return original_call_later(0, callback, *args)
        return original_call_later(delay, callback, *args)

    monkeypatch.setattr(loop, "call_later", recording_call_later)

    with pytest.raises(TimeoutError):
        await f

    assert 30.0 in fired_delays


@pytest.mark.asyncio
async def test_timeout_cancelled_when_future_resolves(monkeypatch) -> None:
    """Timeout handle is cancelled when future completes before timeout fires."""
    f = Future()

    loop = asyncio.get_running_loop()
    original_call_later = loop.call_later
    handle = None

    def capturing_call_later(delay, callback, *args):
        nonlocal handle
        handle = original_call_later(delay, callback, *args)
        return handle

    monkeypatch.setattr(loop, "call_later", capturing_call_later)

    # resolve the future immediately
    loop.call_soon(f.set_result, "done")
    result = await f

    assert result == "done"
    assert handle is not None
    assert handle.cancelled()


@pytest.mark.asyncio
async def test_timeout_fires_via_on_timeout() -> None:
    """_on_timeout sets TimeoutError on the future."""
    f = Future()
    assert not f.done()
    f._on_timeout()
    assert f.done()
    with pytest.raises(TimeoutError):
        await f


@pytest.mark.asyncio
async def test_on_timeout_noop_when_already_done() -> None:
    """_on_timeout is a no-op if future is already resolved."""
    f = Future()
    f.set_result(42)
    f._on_timeout()  # should not raise or overwrite result
    assert await f == 42


# ── wait_all ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_wait_all_resolves_all() -> None:
    """wait_all awaits all futures and returns their results."""
    f1, f2, f3 = Future(), Future(), Future()
    loop = asyncio.get_running_loop()
    loop.call_soon(f1.set_result, 1)
    loop.call_soon(f2.set_result, 2)
    loop.call_soon(f3.set_result, 3)

    results = await Future.wait_all([f1, f2, f3])
    assert results == [1, 2, 3]


@pytest.mark.asyncio
async def test_wait_all_skips_none() -> None:
    """wait_all skips None entries."""
    f = Future()
    asyncio.get_running_loop().call_soon(f.set_result, 99)
    results = await Future.wait_all([None, f, None])
    assert results == [99]
