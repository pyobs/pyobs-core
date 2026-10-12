"""A failed disco#info must not look like "peer has no interfaces" (#952 items 3, 5, 6).

Pure unit tests: no network, no live ejabberd.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import slixmpp.exceptions

from pyobs.comm.dummy import DummyComm
from pyobs.comm.xmpp import XmppComm
from pyobs.events import LogEvent, NewImageEvent
from pyobs.interfaces import IModule, ITelescope

JID = "camera@localhost/pyobs"


def make_comm() -> XmppComm:
    comm = XmppComm.__new__(XmppComm)
    comm._xmpp = MagicMock()
    comm._jid = "gui@localhost/pyobs"
    comm._domain = "localhost"
    comm._resource = "pyobs"
    comm._interface_cache = {}
    comm._interface_features = {}
    comm._peer_sent_events = {}
    comm._discovery_retries = {}
    comm._client_states = {}
    comm._online_clients = []
    comm._presence_callbacks = {}
    comm._event_handlers = {}
    comm._warned_version_mismatches = set()
    comm._send_event_to_module = MagicMock()  # type: ignore[method-assign]
    return comm


def presence_msg() -> dict[str, Any]:
    return {"from": MagicMock(full=JID, username="camera"), "show": "", "status": ""}


# ---------------------------------------------------------------------------
# _get_interfaces: None means "disco#info failed", [] means "no IModule"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exc",
    [
        slixmpp.exceptions.IqTimeout(iq=None),
        slixmpp.exceptions.IqError({"error": {"condition": "service-unavailable", "text": "", "type": "cancel"}}),
    ],
)
async def test_get_interfaces_returns_none_on_iq_failure(exc: Exception) -> None:
    comm = make_comm()
    comm._safe_send = AsyncMock(side_effect=exc)  # type: ignore[method-assign]
    assert await comm._get_interfaces(JID) is None


@pytest.mark.asyncio
async def test_get_interfaces_returns_none_without_answer() -> None:
    comm = make_comm()
    comm._safe_send = AsyncMock(return_value=None)  # type: ignore[method-assign]
    assert await comm._get_interfaces(JID) is None


@pytest.mark.asyncio
async def test_get_interfaces_returns_none_on_malformed_answer() -> None:
    comm = make_comm()
    comm._safe_send = AsyncMock(return_value=object())  # type: ignore[method-assign]
    assert await comm._get_interfaces(JID) is None


@pytest.mark.asyncio
async def test_get_interfaces_returns_empty_list_without_imodule() -> None:
    comm = make_comm()
    comm._safe_send = AsyncMock(return_value={"features": []})  # type: ignore[method-assign]
    with patch("pyobs.comm.xmpp.xmppcomm.asyncio.sleep", new=AsyncMock()):
        assert await comm._get_interfaces(JID) == []


@pytest.mark.asyncio
async def test_get_interfaces_failure_during_recursion_returns_none() -> None:
    comm = make_comm()
    comm._safe_send = AsyncMock(  # type: ignore[method-assign]
        side_effect=[{"features": []}, slixmpp.exceptions.IqTimeout(iq=None)]
    )
    with patch("pyobs.comm.xmpp.xmppcomm.asyncio.sleep", new=AsyncMock()):
        assert await comm._get_interfaces(JID) is None


# ---------------------------------------------------------------------------
# _got_online
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_got_online_failed_disco_keeps_peer_hidden_and_retries() -> None:
    comm = make_comm()
    comm._get_interfaces = AsyncMock(return_value=None)  # type: ignore[method-assign]
    comm._retry_discovery = AsyncMock()  # type: ignore[method-assign]

    await comm._got_online(presence_msg())

    assert comm._online_clients == []
    comm._send_event_to_module.assert_not_called()  # type: ignore[attr-defined]
    assert JID in comm._discovery_retries
    comm._retry_discovery.assert_called_once()
    # no hang, and not a wrong "no interfaces" answer either
    with pytest.raises(IndexError):
        await asyncio.wait_for(comm.get_interfaces(JID), timeout=7.0)


@pytest.mark.asyncio
async def test_got_online_fails_waiting_get_interfaces() -> None:
    comm = make_comm()
    gate = asyncio.Event()

    async def slow(_jid: str) -> None:
        await gate.wait()
        return None

    comm._get_interfaces = slow  # type: ignore[method-assign]
    comm._retry_discovery = AsyncMock()  # type: ignore[method-assign]

    online = asyncio.create_task(comm._got_online(presence_msg()))
    await asyncio.sleep(0)
    waiter = asyncio.create_task(comm.get_interfaces(JID))
    await asyncio.sleep(0)
    gate.set()
    await online

    with pytest.raises(IndexError):
        await asyncio.wait_for(waiter, timeout=2.0)


@pytest.mark.asyncio
async def test_got_online_does_not_start_second_retry() -> None:
    comm = make_comm()
    comm._get_interfaces = AsyncMock(return_value=None)  # type: ignore[method-assign]
    comm._retry_discovery = AsyncMock()  # type: ignore[method-assign]

    await comm._got_online(presence_msg())
    first = comm._discovery_retries[JID]
    await comm._got_online(presence_msg())

    assert comm._discovery_retries[JID] is first
    comm._retry_discovery.assert_called_once()


@pytest.mark.asyncio
async def test_retry_recovers_and_subscribes_to_events() -> None:
    """#952 item 3: disco#info fails first, then works: the peer comes online and its events get subscribed."""
    comm = make_comm()
    comm._event_handlers = {NewImageEvent: [MagicMock()]}
    comm._subscribe_event_with_retry = AsyncMock()  # type: ignore[method-assign]

    results: list[list[str] | None] = [None, ["IModule"]]

    async def get_interfaces(jid: str) -> list[str] | None:
        result = results.pop(0)
        if result is not None:
            comm._peer_sent_events[jid] = {(NewImageEvent.__name__, NewImageEvent.version)}
        return result

    comm._get_interfaces = get_interfaces  # type: ignore[method-assign]

    with patch("pyobs.comm.xmpp.xmppcomm._retry_delay", return_value=0.0):
        await comm._got_online(presence_msg())
        assert comm._online_clients == []
        await asyncio.wait_for(comm._discovery_retries[JID], timeout=2.0)

    assert comm._online_clients == [JID]
    assert JID not in comm._discovery_retries
    comm._send_event_to_module.assert_called_once()  # type: ignore[attr-defined]
    await asyncio.sleep(0)
    comm._subscribe_event_with_retry.assert_called_once_with("camera", NewImageEvent)  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_offline_cancels_retry_and_clears_peer_events() -> None:
    comm = make_comm()
    comm._get_interfaces = AsyncMock(return_value=None)  # type: ignore[method-assign]
    comm._peer_sent_events[JID] = {("NewImageEvent", 1)}

    with patch("pyobs.comm.xmpp.xmppcomm._retry_delay", return_value=60.0):
        await comm._got_online(presence_msg())
        task = comm._discovery_retries[JID]
        await asyncio.sleep(0)
        comm._jid_got_offline(JID)
        await asyncio.sleep(0)

    assert task.cancelled()
    assert JID not in comm._discovery_retries
    assert JID not in comm._peer_sent_events


# ---------------------------------------------------------------------------
# Comm._get_client: an empty proxy must not be cached (item 5)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_proxy_is_not_cached() -> None:
    comm = DummyComm()
    comm.get_interfaces = AsyncMock(side_effect=[[], [IModule, ITelescope]])  # type: ignore[method-assign]

    first = await comm._get_client("telescope")
    assert first is not None
    assert "telescope" not in comm._proxies

    second = await comm._get_client("telescope")
    assert second is not None
    assert comm._proxies["telescope"] is second
    assert isinstance(second, object) and ITelescope in second._interfaces  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# _handle_event: dropped old events are logged (item 6)
# ---------------------------------------------------------------------------


def _event_msg(node: str, age: float) -> Any:
    body = json.dumps(
        {
            "type": "LogEvent",
            "timestamp": time.time() - age,
            "uuid": "u",
            "data": {
                "time": "2026-01-01T00:00:00",
                "level": "INFO",
                "filename": "x.py",
                "function": "f",
                "line": 1,
                "message": "m",
                "sender": "",
            },
        }
    )
    msg: dict[str, Any] = {
        "pubsub_event": {"items": {"item": {"payload": SimpleNamespace(text=body)}}},
    }

    class Msg(dict[str, Any]):
        xml = SimpleNamespace(findall=lambda _ns: [])

    return Msg(msg)


@pytest.mark.asyncio
async def test_old_event_drop_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    comm = XmppComm(jid="user@example.com")
    node = XmppComm._event_node("peer", LogEvent)
    with patch.object(comm, "_send_event_to_module") as send, caplog.at_level(logging.INFO):
        await comm._handle_event(_event_msg(node, age=31.0), node)
    send.assert_not_called()
    assert "Dropping LogEvent from peer" in caplog.text


@pytest.mark.asyncio
async def test_recent_event_is_dispatched() -> None:
    comm = XmppComm(jid="user@example.com")
    node = XmppComm._event_node("peer", LogEvent)
    with patch.object(comm, "_send_event_to_module") as send:
        await comm._handle_event(_event_msg(node, age=29.0), node)
    send.assert_called_once()
