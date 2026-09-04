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

import asyncio
from unittest.mock import AsyncMock

import pytest

from pyobs.comm.comm import Comm
from pyobs.events import LogEvent, ModuleOpenedEvent


def _bare_comm() -> Comm:
    """A Comm with just enough state for register_event()/unregister_event()/
    _send_event_to_module(), without running Comm.__init__ (which pulls in
    logging/proxy/state machinery none of these tests need)."""
    comm = Comm.__new__(Comm)
    comm._event_handlers = {}
    comm._event_handler_tasks = {}
    comm._events_sent = set()
    comm._events_subscribed = set()
    return comm


@pytest.mark.asyncio
async def test_unregister_event_removes_handler() -> None:
    comm = _bare_comm()
    handler = AsyncMock(return_value=True)

    await comm.register_event(ModuleOpenedEvent, handler)
    assert handler in comm._event_handlers[ModuleOpenedEvent]

    await comm.unregister_event(ModuleOpenedEvent, handler)
    assert handler not in comm._event_handlers[ModuleOpenedEvent]


@pytest.mark.asyncio
async def test_unregister_event_stops_delivery() -> None:
    comm = _bare_comm()
    handler = AsyncMock(return_value=True)

    await comm.register_event(ModuleOpenedEvent, handler)
    await comm.unregister_event(ModuleOpenedEvent, handler)

    comm._send_event_to_module(ModuleOpenedEvent(), "camera")
    handler.assert_not_called()


@pytest.mark.asyncio
async def test_unregister_event_only_removes_matching_handler() -> None:
    """Two independent subscribers (e.g. two widget instances for the same
    event type) don't interfere with each other's teardown."""
    comm = _bare_comm()
    handler_a = AsyncMock(return_value=True)
    handler_b = AsyncMock(return_value=True)

    await comm.register_event(ModuleOpenedEvent, handler_a)
    await comm.register_event(ModuleOpenedEvent, handler_b)

    await comm.unregister_event(ModuleOpenedEvent, handler_a)

    assert handler_a not in comm._event_handlers[ModuleOpenedEvent]
    assert handler_b in comm._event_handlers[ModuleOpenedEvent]


@pytest.mark.asyncio
async def test_unregister_event_unknown_handler_does_not_raise() -> None:
    comm = _bare_comm()

    # never registered -- must be a no-op, not an error
    await comm.unregister_event(ModuleOpenedEvent, AsyncMock())


@pytest.mark.asyncio
async def test_unregister_event_drops_subscribed_role_when_last_handler_removed() -> None:
    """Once the last handler for an event is unregistered, the event must no longer be
    advertised as subscribed -- otherwise disco#info keeps telling peers this module still
    wants to receive an event nothing here handles anymore."""
    comm = _bare_comm()
    handler = AsyncMock(return_value=True)

    await comm.register_event(ModuleOpenedEvent, handler)
    assert ModuleOpenedEvent in comm._events_subscribed

    await comm.unregister_event(ModuleOpenedEvent, handler)
    assert ModuleOpenedEvent not in comm._events_subscribed


@pytest.mark.asyncio
async def test_unregister_event_keeps_subscribed_role_while_other_handlers_remain() -> None:
    """Two independent subscribers for the same event: one tearing down must not un-declare
    the event for the other."""
    comm = _bare_comm()
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
    comm = _bare_comm()
    handler = AsyncMock(return_value=True)

    await comm.register_event(ModuleOpenedEvent)
    await comm.register_event(ModuleOpenedEvent, handler)
    await comm.unregister_event(ModuleOpenedEvent, handler)

    assert ModuleOpenedEvent in comm._events_sent
    assert ModuleOpenedEvent not in comm._events_subscribed


@pytest.mark.asyncio
async def test_unregister_event_cancels_pending_dispatch_task() -> None:
    """A handler dispatch already scheduled via _send_event_to_module() before
    unregister_event() runs in the same synchronous stretch (no await in between)
    must not fire later against a handler that's already torn down -- issue #871."""
    comm = _bare_comm()
    ran = False

    async def handler(event: object, sender: str) -> bool:
        nonlocal ran
        ran = True
        return True

    await comm.register_event(ModuleOpenedEvent, handler)

    comm._send_event_to_module(ModuleOpenedEvent(), "camera")
    tasks = comm._event_handler_tasks[(ModuleOpenedEvent, handler)]
    assert len(tasks) == 1
    task = next(iter(tasks))

    # unregister in the same synchronous stretch, before the scheduled task gets a turn
    await comm.unregister_event(ModuleOpenedEvent, handler)
    assert (ModuleOpenedEvent, handler) not in comm._event_handler_tasks

    await asyncio.sleep(0)
    assert task.cancelled()
    assert ran is False


@pytest.mark.asyncio
async def test_unregister_event_cancels_every_pending_task_for_handler() -> None:
    """Two events for the same (event_class, handler) can be in flight at once (e.g. two
    NewImageEvents arriving back-to-back before the widget is torn down) -- unregistering
    must cancel all of them, not just one, so the tracking set's cancel-loop is exercised
    with more than a single element."""
    comm = _bare_comm()
    run_count = 0

    async def handler(event: object, sender: str) -> bool:
        nonlocal run_count
        run_count += 1
        return True

    await comm.register_event(ModuleOpenedEvent, handler)

    comm._send_event_to_module(ModuleOpenedEvent(), "camera")
    comm._send_event_to_module(ModuleOpenedEvent(), "camera")
    tasks = list(comm._event_handler_tasks[(ModuleOpenedEvent, handler)])
    assert len(tasks) == 2

    await comm.unregister_event(ModuleOpenedEvent, handler)
    assert (ModuleOpenedEvent, handler) not in comm._event_handler_tasks

    await asyncio.sleep(0)
    assert all(task.cancelled() for task in tasks)
    assert run_count == 0


@pytest.mark.asyncio
async def test_unregister_event_leaves_other_event_types_task_pending() -> None:
    """Unregistering a handler for one event type must not cancel its still-pending
    dispatch for a different event type the same handler is also registered for."""
    comm = _bare_comm()

    async def handler(event: object, sender: str) -> bool:
        return True

    await comm.register_event(LogEvent, handler)
    await comm.register_event(ModuleOpenedEvent, handler)

    comm._send_event_to_module(LogEvent("t", "INFO", "f.py", "fn", 1, "msg"), "camera")
    comm._send_event_to_module(ModuleOpenedEvent(), "camera")

    await comm.unregister_event(LogEvent, handler)

    assert (LogEvent, handler) not in comm._event_handler_tasks
    assert (ModuleOpenedEvent, handler) in comm._event_handler_tasks
    other_task = next(iter(comm._event_handler_tasks[(ModuleOpenedEvent, handler)]))
    assert not other_task.cancelled()

    await asyncio.sleep(0)  # let both tasks finish so nothing's left pending at teardown


@pytest.mark.asyncio
async def test_event_handler_task_bookkeeping_cleared_after_completion() -> None:
    """A dispatch task's (event_class, handler) bookkeeping entry must disappear once the
    task completes normally, not just on cancellation -- otherwise _event_handler_tasks
    grows one entry per handler forever on a long-running module, each holding a strong
    reference to that handler (and, transitively, whatever object it's bound to)."""
    comm = _bare_comm()

    async def handler(event: object, sender: str) -> bool:
        return True

    await comm.register_event(ModuleOpenedEvent, handler)

    comm._send_event_to_module(ModuleOpenedEvent(), "camera")
    task = next(iter(comm._event_handler_tasks[(ModuleOpenedEvent, handler)]))

    # _log_handler_exception (registered as this task's done-callback before this point)
    # runs its cleanup before our own await below resumes, since done-callbacks fire in
    # the order they were added.
    await task
    assert (ModuleOpenedEvent, handler) not in comm._event_handler_tasks


@pytest.mark.asyncio
async def test_unregister_event_expands_derived_events() -> None:
    """unregister must mirror the exact same derived-events expansion register_event
    uses, so it can find everything a matching register_event() call added."""
    comm = _bare_comm()
    handler = AsyncMock(return_value=True)

    await comm.register_event(LogEvent, handler)
    assert handler in comm._event_handlers[LogEvent]

    await comm.unregister_event(LogEvent, handler)
    assert handler not in comm._event_handlers[LogEvent]
