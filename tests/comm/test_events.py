"""Tests for Comm.register_event / unregister_event.

Covers https://github.com/pyobs/pyobs-core/issues/438: register_event() had no
inverse, so a caller (e.g. a GUI widget torn down on client disconnect) could
never stop receiving events -- the stale handler stayed in _event_handlers
forever, keeping the caller alive and firing on every future matching event.

Uses ModuleOpenedEvent/LogEvent (real pyobs.events members with no subclasses)
rather than a locally-defined Event subclass -- Comm._get_derived_events()
scans pyobs.events' own namespace for subclasses of the given class, so a
class that isn't itself reachable from pyobs.events would resolve to an empty
list and never actually reach _event_handlers.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pyobs.comm.comm import Comm
from pyobs.events import LogEvent, ModuleOpenedEvent


@pytest.mark.asyncio
async def test_unregister_event_removes_handler() -> None:
    comm = Comm.__new__(Comm)
    comm._event_handlers = {}
    comm._events_sent = set()
    comm._events_subscribed = set()
    handler = AsyncMock(return_value=True)

    await comm.register_event(ModuleOpenedEvent, handler)
    assert handler in comm._event_handlers[ModuleOpenedEvent]

    await comm.unregister_event(ModuleOpenedEvent, handler)
    assert handler not in comm._event_handlers[ModuleOpenedEvent]


@pytest.mark.asyncio
async def test_unregister_event_stops_delivery() -> None:
    comm = Comm.__new__(Comm)
    comm._event_handlers = {}
    comm._events_sent = set()
    comm._events_subscribed = set()
    handler = AsyncMock(return_value=True)

    await comm.register_event(ModuleOpenedEvent, handler)
    await comm.unregister_event(ModuleOpenedEvent, handler)

    comm._send_event_to_module(ModuleOpenedEvent(), "camera")
    handler.assert_not_called()


@pytest.mark.asyncio
async def test_unregister_event_only_removes_matching_handler() -> None:
    """Two independent subscribers (e.g. two widget instances for the same
    event type) don't interfere with each other's teardown."""
    comm = Comm.__new__(Comm)
    comm._event_handlers = {}
    comm._events_sent = set()
    comm._events_subscribed = set()
    handler_a = AsyncMock(return_value=True)
    handler_b = AsyncMock(return_value=True)

    await comm.register_event(ModuleOpenedEvent, handler_a)
    await comm.register_event(ModuleOpenedEvent, handler_b)

    await comm.unregister_event(ModuleOpenedEvent, handler_a)

    assert handler_a not in comm._event_handlers[ModuleOpenedEvent]
    assert handler_b in comm._event_handlers[ModuleOpenedEvent]


@pytest.mark.asyncio
async def test_unregister_event_unknown_handler_does_not_raise() -> None:
    comm = Comm.__new__(Comm)
    comm._event_handlers = {}
    comm._events_sent = set()
    comm._events_subscribed = set()

    # never registered -- must be a no-op, not an error
    await comm.unregister_event(ModuleOpenedEvent, AsyncMock())


@pytest.mark.asyncio
async def test_unregister_event_drops_subscribed_role_when_last_handler_removed() -> None:
    """Once the last handler for an event is unregistered, the event must no longer be
    advertised as subscribed -- otherwise disco#info keeps telling peers this module still
    wants to receive an event nothing here handles anymore."""
    comm = Comm.__new__(Comm)
    comm._event_handlers = {}
    comm._events_sent = set()
    comm._events_subscribed = set()
    handler = AsyncMock(return_value=True)

    await comm.register_event(ModuleOpenedEvent, handler)
    assert ModuleOpenedEvent in comm._events_subscribed

    await comm.unregister_event(ModuleOpenedEvent, handler)
    assert ModuleOpenedEvent not in comm._events_subscribed


@pytest.mark.asyncio
async def test_unregister_event_keeps_subscribed_role_while_other_handlers_remain() -> None:
    """Two independent subscribers for the same event: one tearing down must not un-declare
    the event for the other."""
    comm = Comm.__new__(Comm)
    comm._event_handlers = {}
    comm._events_sent = set()
    comm._events_subscribed = set()
    handler_a = AsyncMock(return_value=True)
    handler_b = AsyncMock(return_value=True)

    await comm.register_event(ModuleOpenedEvent, handler_a)
    await comm.register_event(ModuleOpenedEvent, handler_b)

    await comm.unregister_event(ModuleOpenedEvent, handler_a)

    assert ModuleOpenedEvent in comm._events_subscribed


@pytest.mark.asyncio
async def test_unregister_event_leaves_sent_role_untouched() -> None:
    """A module that both sends an event (handler-less register_event()) and separately
    subscribes to it keeps advertising it as sent even after its subscription is torn down."""
    comm = Comm.__new__(Comm)
    comm._event_handlers = {}
    comm._events_sent = set()
    comm._events_subscribed = set()
    handler = AsyncMock(return_value=True)

    await comm.register_event(ModuleOpenedEvent)
    await comm.register_event(ModuleOpenedEvent, handler)
    await comm.unregister_event(ModuleOpenedEvent, handler)

    assert ModuleOpenedEvent in comm._events_sent
    assert ModuleOpenedEvent not in comm._events_subscribed


@pytest.mark.asyncio
async def test_unregister_event_expands_derived_events() -> None:
    """unregister must mirror the exact same derived-events expansion register_event
    uses, so it can find everything a matching register_event() call added."""
    comm = Comm.__new__(Comm)
    comm._event_handlers = {}
    comm._events_sent = set()
    comm._events_subscribed = set()
    handler = AsyncMock(return_value=True)

    await comm.register_event(LogEvent, handler)
    assert handler in comm._event_handlers[LogEvent]

    await comm.unregister_event(LogEvent, handler)
    assert handler not in comm._event_handlers[LogEvent]
