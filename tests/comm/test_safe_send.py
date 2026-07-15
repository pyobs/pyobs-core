"""Tests for XmppComm._safe_send's retry/timeout handling.

Covers https://github.com/pyobs/pyobs-core/issues/664: _safe_send must not
hang forever if the underlying slixmpp call never resolves and slixmpp's own
IQ timeout fails to fire -- it needs its own bound via asyncio.wait_for.
"""

from __future__ import annotations

import asyncio

import pytest
import slixmpp.exceptions

from pyobs.comm.xmpp.xmppcomm import XmppComm


def make_xmpp_comm(attempts: int = 3, wait: float = 0.01, timeout: float = 0.05) -> XmppComm:
    """Create a minimal XmppComm instance for testing, without a live connection."""
    comm = XmppComm.__new__(XmppComm)
    comm._safe_send_attempts = attempts
    comm._safe_send_wait = wait
    comm._safe_send_timeout = timeout
    return comm


@pytest.mark.asyncio
async def test_safe_send_returns_result_on_success() -> None:
    comm = make_xmpp_comm()

    async def method() -> str:
        return "ok"

    assert await comm._safe_send(method) == "ok"


@pytest.mark.asyncio
async def test_safe_send_retries_and_raises_on_iq_timeout() -> None:
    comm = make_xmpp_comm(attempts=3)
    calls = 0

    async def method() -> None:
        nonlocal calls
        calls += 1
        raise slixmpp.exceptions.IqTimeout(iq=None)

    with pytest.raises(slixmpp.exceptions.IqTimeout):
        await comm._safe_send(method)

    assert calls == 3


@pytest.mark.asyncio
async def test_safe_send_enforces_own_timeout_when_method_hangs() -> None:
    """A method that never returns (e.g. slixmpp's own IQ timeout not firing) must
    still be bounded by _safe_send's own timeout, not hang forever."""
    comm = make_xmpp_comm(attempts=2, wait=0.01, timeout=0.05)
    calls = 0

    async def method() -> None:
        nonlocal calls
        calls += 1
        await asyncio.sleep(10)

    with pytest.raises(slixmpp.exceptions.IqTimeout):
        await asyncio.wait_for(comm._safe_send(method), timeout=1.0)

    assert calls == 2


@pytest.mark.asyncio
async def test_safe_send_succeeds_after_own_timeout_then_recovery() -> None:
    comm = make_xmpp_comm(attempts=3, wait=0.01, timeout=0.05)
    calls = 0

    async def method() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            await asyncio.sleep(10)
        return "ok"

    result = await asyncio.wait_for(comm._safe_send(method), timeout=1.0)
    assert result == "ok"
    assert calls == 2
