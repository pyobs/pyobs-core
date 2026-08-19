"""XmppComm._handle_event must tolerate pubsub notifications without a payload.

Retract stanzas, node purges, and nodes with deliver_payloads off arrive as
notifications whose <item> has no <payload> element (or no <item> at all). slixmpp
leaves the corresponding accessors at None; _handle_event must skip them instead of
raising AttributeError on None.text -- which previously surfaced as a "Task exception
was never retrieved" ERROR from the fire-and-forget task in _handle_event_sync.

Pure unit tests: no network, no live ejabberd -- _handle_event is called directly
with stub message dicts.
"""

from __future__ import annotations

import asyncio
import json
import time
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from pyobs.comm.xmpp import XmppComm
from pyobs.comm.xmpp.xmppcomm import _log_task_exception
from pyobs.events import LogEvent


def _make_comm() -> XmppComm:
    return XmppComm(jid="user@example.com")


class _EventMsg(dict[str, Any]):
    """Stub pubsub notification: dict-style mapping access (like slixmpp's stanza
    accessors) plus an .xml attribute for the raw-XML lookups."""


def _event_msg(node: str, payload_text: str | None) -> _EventMsg:
    """Stub pubsub event notification message, mirroring slixmpp's mapping access.

    slixmpp stanza accessors return None for absent elements rather than raising
    KeyError, so a payload-less <item> is modeled as item["payload"] is None.
    payload_text is the raw text of the <payload> element slixmpp would expose.
    """
    msg = _EventMsg(
        pubsub_event={
            "items": {"item": {"payload": None if payload_text is None else SimpleNamespace(text=payload_text)}}
        }
    )
    msg.xml = SimpleNamespace(findall=lambda _ns: [])  # no <delay> elements
    return msg


def _log_event_json(message: str) -> str:
    return json.dumps(
        {
            "type": "LogEvent",
            "timestamp": time.time(),
            "uuid": "some-uuid",
            "data": {
                "time": "2026-01-01T00:00:00",
                "level": "INFO",
                "filename": "x.py",
                "function": "f",
                "line": 1,
                "message": message,
                "sender": "",
            },
        }
    )


@pytest.mark.asyncio
async def test_payloadless_item_is_skipped() -> None:
    """A retract-style notification (item without payload) must not raise or dispatch."""
    comm = _make_comm()
    node = XmppComm._event_node("peer", LogEvent)
    with patch.object(comm, "_send_event_to_module") as send:
        await comm._handle_event(_event_msg(node, payload_text=None), node)
        send.assert_not_called()


@pytest.mark.asyncio
async def test_missing_item_is_skipped() -> None:
    """A retract-style notification (no <item> at all) must not raise or dispatch."""
    comm = _make_comm()
    node = XmppComm._event_node("peer", LogEvent)
    msg = _event_msg(node, payload_text=None)
    msg["pubsub_event"]["items"]["item"] = None
    with patch.object(comm, "_send_event_to_module") as send:
        await comm._handle_event(msg, node)
        send.assert_not_called()


@pytest.mark.asyncio
async def test_missing_items_is_skipped() -> None:
    """A purge-style notification (no <items> element at all) must not raise or dispatch."""
    comm = _make_comm()
    node = XmppComm._event_node("peer", LogEvent)
    msg = _event_msg(node, payload_text=None)
    msg["pubsub_event"]["items"] = None
    with patch.object(comm, "_send_event_to_module") as send:
        await comm._handle_event(msg, node)
        send.assert_not_called()


@pytest.mark.asyncio
async def test_payload_notification_is_dispatched() -> None:
    """A normal notification with a payload is still parsed and dispatched."""
    comm = _make_comm()
    node = XmppComm._event_node("peer", LogEvent)
    with patch.object(comm, "_send_event_to_module") as send:
        await comm._handle_event(_event_msg(node, _log_event_json("hello")), node)
    send.assert_called_once()
    event, from_module = send.call_args.args
    assert from_module == "peer"
    assert isinstance(event, LogEvent)
    assert event.message == "hello"


@pytest.mark.asyncio
async def test_log_task_exception_retrieves_and_logs() -> None:
    """_log_task_exception must retrieve a failed task's exception (no "never retrieved"
    noise) and log it with exc_info."""

    async def boom() -> None:
        raise AttributeError("boom")

    task = asyncio.create_task(boom())
    while not task.done():
        await asyncio.sleep(0)

    with patch("pyobs.comm.xmpp.xmppcomm.log") as log:
        _log_task_exception(task)

    log.error.assert_called_once()
    assert log.error.call_args.kwargs["exc_info"] is not None


@pytest.mark.asyncio
async def test_log_task_exception_ignores_cancelled() -> None:
    """A cancelled task must not raise inside the callback."""

    async def never() -> None:
        await asyncio.sleep(60)

    task = asyncio.create_task(never())
    task.cancel()
    while not task.done():
        await asyncio.sleep(0)
    with patch("pyobs.comm.xmpp.xmppcomm.log") as log:
        _log_task_exception(task)
    log.error.assert_not_called()
