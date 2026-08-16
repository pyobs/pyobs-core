"""Integration tests for explicit pubsub event subscriptions.

Covers specs/adrs/0012-event-delivery-explicit-pubsub-subscription-not-presence.md /
specs/plans/2026-08-16-explicit-pubsub-event-subscriptions.md: events are published/subscribed
via the shared pubsub.<domain> service (same mechanism as state), not XEP-0163 PEP, so delivery
is gated by an explicit subscription instead of presence.

Requires a live ejabberd server with a third registered user ("control") in addition to the
usual "camera"/"observer" -- see tests/xmpp/docker-compose.yml. Run with:

    PYOBS_TEST_XMPP_HOST=localhost PYOBS_TEST_XMPP_DOMAIN=localhost \\
    pytest -m xmpp tests/integration/test_xmpp_event_subscriptions.py -v
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from pyobs.comm.xmpp.xmppcomm import XmppComm
from pyobs.events import BadWeatherEvent, LogEvent, ModuleClosedEvent, ModuleOpenedEvent
from pyobs.interfaces import IModule
from pyobs.utils.enums import ModuleState

pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.xmpp]


def _named_module(name: str, comm) -> MagicMock:
    """Minimal module stub with a *real* name matching the comm's own JID user --
    needed here (unlike tests/integration/conftest.py's make_module, which hardcodes
    "camera") because event node ids embed the publishing module's name and must match
    what subscribers derive from the peer's JID."""
    m = MagicMock()
    m.interfaces = [IModule]
    m.name = name
    comm.module = m
    return m


async def wait_for(condition, *, timeout: float = 15.0, interval: float = 0.1) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        if condition():
            return True
        await asyncio.sleep(interval)
    return False


async def wait_for_peer(comm, peer: str, *, timeout: float = 15.0) -> None:
    ok = await wait_for(lambda: peer in comm.clients, timeout=timeout)
    assert ok, f"{peer!r} did not appear in client list within {timeout}s"


def _log_event(message: str) -> LogEvent:
    return LogEvent(time="2026-08-16T00:00:00", level="INFO", filename="x.py", function="f", line=1, message=message)


async def test_handler_receives_event_from_peer(make_xmpp_comm, make_unopened_comm) -> None:
    """A module with a registered LogEvent handler receives events published by a peer."""

    async def _run():
        camera_comm = make_unopened_comm("camera")
        _named_module("camera", camera_comm)
        camera_comm = await make_xmpp_comm("camera", comm=camera_comm)
        await camera_comm.set_presence(ModuleState.READY)

        control_comm = make_unopened_comm("control")
        _named_module("control", control_comm)
        control_comm = await make_xmpp_comm("control", comm=control_comm)
        await control_comm.set_presence(ModuleState.READY)

        await wait_for_peer(camera_comm, "control")

        received: list = []

        async def handler(event, from_client) -> bool:
            received.append((event, from_client))
            return True

        await camera_comm.register_event(LogEvent, handler)

        # give the background subscribe-with-retry task time to complete
        await asyncio.sleep(1.0)

        await control_comm.send_event(_log_event("hello"))

        ok = await wait_for(lambda: len(received) >= 1)
        assert ok, "camera did not receive LogEvent from control"
        event, from_client = received[0]
        assert event.data["message"] == "hello"
        assert from_client == "control"

    await asyncio.wait_for(_run(), timeout=60)


async def test_non_subscriber_never_gets_the_wire_message(make_xmpp_comm, make_unopened_comm) -> None:
    """A module that never registered a LogEvent handler must not even receive the pubsub
    notification on the wire -- not "receives and drops", actually never delivered."""

    async def _run():
        observer_comm = make_unopened_comm("observer")
        _named_module("observer", observer_comm)

        sync_calls: list = []
        original = XmppComm._handle_event_sync

        def spy(self, msg):
            sync_calls.append(self)
            return original(self, msg)

        with patch.object(XmppComm, "_handle_event_sync", spy):
            observer_comm = await make_xmpp_comm("observer", comm=observer_comm)
            await observer_comm.set_presence(ModuleState.READY)

            control_comm = make_unopened_comm("control")
            _named_module("control", control_comm)
            control_comm = await make_xmpp_comm("control", comm=control_comm)
            await control_comm.set_presence(ModuleState.READY)

            await wait_for_peer(observer_comm, "control")

            # observer registers no LogEvent handler at all
            await asyncio.sleep(1.0)

            await control_comm.send_event(_log_event("nobody should see this"))

            # give it a real chance to arrive if delivery were (incorrectly) presence-based
            await asyncio.sleep(2.0)

            observer_sync_calls = [c for c in sync_calls if c is observer_comm]
            assert observer_sync_calls == [], (
                f"observer's _handle_event_sync fired {len(observer_sync_calls)}x for an event "
                "it never subscribed to -- delivery is not actually filtered"
            )

    await asyncio.wait_for(_run(), timeout=60)


async def test_late_registered_handler_still_receives_events(make_xmpp_comm, make_unopened_comm) -> None:
    """Registering a handler after a peer is already online must still result in a subscription
    (covered by _got_online re-subscribing peers already online at registration time)."""

    async def _run():
        control_comm = make_unopened_comm("control")
        _named_module("control", control_comm)
        control_comm = await make_xmpp_comm("control", comm=control_comm)
        await control_comm.set_presence(ModuleState.READY)

        camera_comm = make_unopened_comm("camera")
        _named_module("camera", camera_comm)
        camera_comm = await make_xmpp_comm("camera", comm=camera_comm)
        await camera_comm.set_presence(ModuleState.READY)

        await wait_for_peer(camera_comm, "control")

        # control has been online for a while before camera ever registers a handler
        await asyncio.sleep(0.5)

        received: list = []

        async def handler(event, from_client) -> bool:
            received.append((event, from_client))
            return True

        await camera_comm.register_event(LogEvent, handler)
        await asyncio.sleep(1.0)

        await control_comm.send_event(_log_event("late subscribe"))

        ok = await wait_for(lambda: len(received) >= 1)
        assert ok, "camera did not receive LogEvent after late handler registration"

    await asyncio.wait_for(_run(), timeout=60)


async def test_unregister_stops_delivery(make_xmpp_comm, make_unopened_comm) -> None:
    """After the last handler for an event class is removed, no further events must arrive."""

    async def _run():
        camera_comm = make_unopened_comm("camera")
        _named_module("camera", camera_comm)
        camera_comm = await make_xmpp_comm("camera", comm=camera_comm)
        await camera_comm.set_presence(ModuleState.READY)

        control_comm = make_unopened_comm("control")
        _named_module("control", control_comm)
        control_comm = await make_xmpp_comm("control", comm=control_comm)
        await control_comm.set_presence(ModuleState.READY)

        await wait_for_peer(camera_comm, "control")

        received: list = []

        async def handler(event, from_client) -> bool:
            received.append((event, from_client))
            return True

        await camera_comm.register_event(LogEvent, handler)
        await asyncio.sleep(1.0)

        await control_comm.send_event(_log_event("before unregister"))
        ok = await wait_for(lambda: len(received) >= 1)
        assert ok, "camera did not receive LogEvent before unregister"

        await camera_comm.unregister_event(LogEvent, handler)
        await asyncio.sleep(1.0)

        await control_comm.send_event(_log_event("after unregister"))
        await asyncio.sleep(2.0)

        assert len(received) == 1, f"expected exactly 1 event (before unregister), got {len(received)}"

    await asyncio.wait_for(_run(), timeout=60)


async def test_local_event_handler_never_subscribes(make_xmpp_comm, make_unopened_comm) -> None:
    """Registering a handler for a local event (e.g. ModuleOpenedEvent/ModuleClosedEvent, which
    every real Module does via module.py/comm.py) must not attempt to subscribe to a peer's
    node. Local events are synthesized directly in _got_online/_jid_got_offline, never published
    to pubsub -- subscribing would retry forever against a node that will never exist."""

    async def _run():
        camera_comm = make_unopened_comm("camera")
        _named_module("camera", camera_comm)
        camera_comm = await make_xmpp_comm("camera", comm=camera_comm)
        await camera_comm.set_presence(ModuleState.READY)

        async def handler(event, from_client) -> bool:
            return True

        await camera_comm.register_event(ModuleOpenedEvent, handler)

        control_comm = make_unopened_comm("control")
        _named_module("control", control_comm)
        control_comm = await make_xmpp_comm("control", comm=control_comm)
        await control_comm.set_presence(ModuleState.READY)

        await wait_for_peer(camera_comm, "control")
        await asyncio.sleep(1.0)

        assert (
            camera_comm._event_subscriptions == set()
        ), f"camera attempted a pubsub subscribe for a local event: {camera_comm._event_subscriptions}"

    await asyncio.wait_for(_run(), timeout=60)


async def test_module_opened_and_closed_events_still_fire(make_xmpp_comm, make_unopened_comm) -> None:
    """Local events must be unaffected by moving regular events onto the shared pubsub service --
    they never touched pubsub either way."""

    async def _run():
        camera_comm = make_unopened_comm("camera")
        _named_module("camera", camera_comm)
        camera_comm = await make_xmpp_comm("camera", comm=camera_comm)
        await camera_comm.set_presence(ModuleState.READY)

        opened: list = []
        closed: list = []

        async def opened_handler(event, from_client) -> bool:
            opened.append(from_client)
            return True

        async def closed_handler(event, from_client) -> bool:
            closed.append(from_client)
            return True

        await camera_comm.register_event(ModuleOpenedEvent, opened_handler)
        await camera_comm.register_event(ModuleClosedEvent, closed_handler)

        control_comm = make_unopened_comm("control")
        _named_module("control", control_comm)
        control_comm = await make_xmpp_comm("control", comm=control_comm)
        await control_comm.set_presence(ModuleState.READY)

        assert await wait_for(lambda: "control" in opened), "ModuleOpenedEvent did not fire for control"

        await control_comm.close()

        assert await wait_for(lambda: "control" in closed), "ModuleClosedEvent did not fire for control"

    await asyncio.wait_for(_run(), timeout=60)


async def test_restart_resubscribes_to_already_online_peer(make_xmpp_comm, make_unopened_comm) -> None:
    """After a subscriber restarts (new session, same bare JID), it must resume receiving events
    from a peer that stayed online throughout, with no special handling needed -- the new
    session's own _got_online firing for each already-online peer covers it."""

    async def _run():
        control_comm = make_unopened_comm("control")
        _named_module("control", control_comm)
        control_comm = await make_xmpp_comm("control", comm=control_comm)
        await control_comm.set_presence(ModuleState.READY)

        camera_comm = make_unopened_comm("camera")
        _named_module("camera", camera_comm)
        camera_comm = await make_xmpp_comm("camera", comm=camera_comm)
        await camera_comm.set_presence(ModuleState.READY)

        await wait_for_peer(camera_comm, "control")

        async def handler(event, from_client) -> bool:
            pass

        await camera_comm.register_event(LogEvent, handler)
        await asyncio.sleep(1.0)

        # restart: close the first session, open a fresh one under the same JID
        await camera_comm.close()
        await asyncio.sleep(0.5)

        camera_comm2 = make_unopened_comm("camera")
        _named_module("camera", camera_comm2)
        camera_comm2 = await make_xmpp_comm("camera", comm=camera_comm2)
        await camera_comm2.set_presence(ModuleState.READY)

        received2: list = []

        async def handler2(event, from_client) -> bool:
            received2.append((event, from_client))
            return True

        await camera_comm2.register_event(LogEvent, handler2)

        await wait_for_peer(camera_comm2, "control")
        await asyncio.sleep(1.0)

        await control_comm.send_event(_log_event("after restart"))

        ok = await wait_for(lambda: len(received2) >= 1)
        assert ok, "camera did not receive LogEvent after restarting with a fresh session"

    await asyncio.wait_for(_run(), timeout=60)


async def test_peer_not_advertising_send_never_subscribed(make_xmpp_comm, make_unopened_comm) -> None:
    """A module must not subscribe to a peer's node for an event type that peer never declared
    as "send" in its disco#info -- e.g. a camera's BadWeatherEvent handler must not retry-subscribe
    to a peer that only ever receives (or never registered) BadWeatherEvent, since that node will
    never be created. See _peer_sent_events / _get_disco_info's role="send" tagging."""

    async def _run():
        camera_comm = make_unopened_comm("camera")
        _named_module("camera", camera_comm)
        camera_comm = await make_xmpp_comm("camera", comm=camera_comm)
        await camera_comm.set_presence(ModuleState.READY)

        async def handler(event, from_client) -> bool:
            return True

        await camera_comm.register_event(BadWeatherEvent, handler)

        control_comm = make_unopened_comm("control")
        _named_module("control", control_comm)
        control_comm = await make_xmpp_comm("control", comm=control_comm)
        await control_comm.set_presence(ModuleState.READY)

        await wait_for_peer(camera_comm, "control")
        # give the (would-be) background subscribe-with-retry task time to fire if the gate
        # were missing
        await asyncio.sleep(1.0)

        assert ("control", BadWeatherEvent) not in camera_comm._event_subscriptions, (
            "camera subscribed to control's BadWeatherEvent node even though control never " "advertised sending it"
        )

    await asyncio.wait_for(_run(), timeout=60)


async def test_handler_receives_event_from_send_only_peer(make_xmpp_comm, make_unopened_comm) -> None:
    """The flip side of test_peer_not_advertising_send_never_subscribed: a peer that registers an
    event handler-less (declaring it only sends, never subscribes) still gets subscribed to and
    delivers events normally -- the gate keys off the peer's advertised "send" role, not off
    whether the subscriber itself ever received a matching disco feature some other way."""

    async def _run():
        control_comm = make_unopened_comm("control")
        _named_module("control", control_comm)
        control_comm = await make_xmpp_comm("control", comm=control_comm)
        await control_comm.set_presence(ModuleState.READY)
        # handler-less register_event: declares "send" role only, no subscription of its own
        await control_comm.register_event(BadWeatherEvent)

        camera_comm = make_unopened_comm("camera")
        _named_module("camera", camera_comm)
        camera_comm = await make_xmpp_comm("camera", comm=camera_comm)
        await camera_comm.set_presence(ModuleState.READY)

        received: list = []

        async def handler(event, from_client) -> bool:
            received.append((event, from_client))
            return True

        await camera_comm.register_event(BadWeatherEvent, handler)
        await wait_for_peer(camera_comm, "control")
        await asyncio.sleep(1.0)

        await control_comm.send_event(BadWeatherEvent())

        ok = await wait_for(lambda: len(received) >= 1)
        assert ok, "camera did not receive BadWeatherEvent from a peer that declared it as send-only"

    await asyncio.wait_for(_run(), timeout=60)
