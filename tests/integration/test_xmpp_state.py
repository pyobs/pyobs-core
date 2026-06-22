"""Integration tests for the XEP-0060 state pub/sub path.

Requires a live ejabberd server with two pre-registered accounts:
  camera@<domain>   — the module that owns and publishes state
  observer@<domain> — the client that subscribes and reads state

Set PYOBS_TEST_XMPP_HOST (and optionally PYOBS_TEST_XMPP_DOMAIN /
PYOBS_TEST_XMPP_PORT / PYOBS_TEST_XMPP_PASSWORD) to enable.

For a self-contained local server use the docker-compose in tests/xmpp/:
  docker compose -f tests/xmpp/docker-compose.yml up -d

Account registration is handled by the CTL_ON_CREATE hook in that file.
For a hand-run server, register the accounts manually:
  ejabberdctl register camera   <domain> pyobs
  ejabberdctl register observer <domain> pyobs
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from pyobs.events import ModuleClosedEvent
from pyobs.interfaces import ICooling, IModule
from pyobs.interfaces.ICooling import CoolingState

# Applies asyncio/integration/xmpp marks to every test in this module.
# asyncio must be in pytestmark (not added via pytest_collection_modifyitems)
# because pytest-asyncio strict mode requires the mark at definition time.
pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.xmpp]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def make_module(interfaces: list) -> MagicMock:
    """Minimal module stub satisfying what XmppComm needs on connect.

    IModule must be included: XmppComm._get_interfaces() only adds a peer to
    _online_clients once it sees IModule in the disco#info features — without
    it the peer never appears in comm.clients regardless of other interfaces.
    """
    m = MagicMock()
    # Always include IModule so _got_online completes successfully
    m.interfaces = list({IModule} | set(interfaces))
    m.name = "camera"
    return m


async def wait_for(condition, *, timeout: float = 10.0, interval: float = 0.1) -> bool:
    """Poll *condition* until truthy or *timeout* seconds elapse."""
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        if condition():
            return True
        await asyncio.sleep(interval)
    return False


async def wait_for_peer(comm, peer: str, *, timeout: float = 15.0) -> None:
    """Wait until *comm* sees *peer* in its client list (presence + disco#info done)."""
    ok = await wait_for(lambda: peer in comm.clients, timeout=timeout)
    assert ok, f"{peer!r} did not appear in client list within {timeout}s"


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


async def test_subscriber_receives_initial_value_on_subscribe(make_xmpp_comm) -> None:
    """
    A subscriber that connects after the first publish must receive the current
    value immediately on subscribe (send_last_published_item semantics).
    """

    async def _run():
        camera_comm = await make_xmpp_comm("camera", make_module([ICooling]))
        await camera_comm.set_state(ICooling, CoolingState(setpoint=-20.0, power=65, enabled=True))

        # Brief pause to let ejabberd persist the item before observer subscribes
        await asyncio.sleep(0.5)

        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        received: list[CoolingState] = []
        await observer_comm.subscribe_state("camera", ICooling, received.append)

        assert await wait_for(lambda: len(received) > 0), "No state received within timeout"
        assert received[0].enabled is True

    await asyncio.wait_for(_run(), timeout=60)


async def test_subscriber_receives_live_update(make_xmpp_comm) -> None:
    """After subscribing, subsequent set_state calls must arrive at the subscriber."""

    async def _run():
        camera_comm = await make_xmpp_comm("camera", make_module([ICooling]))
        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        received: list[CoolingState] = []
        await observer_comm.subscribe_state("camera", ICooling, received.append)

        await camera_comm.set_state(ICooling, CoolingState(setpoint=-10.0, power=30, enabled=True))
        # Wait for first update before publishing second — ejabberd's max_items:1
        # means rapid back-to-back publishes may coalesce into a single notification.
        assert await wait_for(lambda: len(received) >= 1), "First update not received"

        await camera_comm.set_state(ICooling, CoolingState(setpoint=-25.0, power=80, enabled=True))
        assert await wait_for(lambda: len(received) >= 2), "Second update not received"

    await asyncio.wait_for(_run(), timeout=60)


async def test_proxy_state_method_reflects_latest_value(make_xmpp_comm) -> None:
    """proxy.state(ICooling) must return the latest value without an RPC round-trip."""

    async def _run():
        camera_comm = await make_xmpp_comm("camera", make_module([ICooling]))
        await camera_comm.set_state(ICooling, CoolingState(setpoint=-15.0, power=50, enabled=True))
        await asyncio.sleep(0.5)

        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        async with observer_comm.proxy("camera", ICooling) as camera:
            assert await wait_for(lambda: camera.state(ICooling) is not None), "Proxy state never populated"

    await asyncio.wait_for(_run(), timeout=60)


async def test_disconnect_cleans_up_subscriptions(make_xmpp_comm) -> None:
    """
    When the remote module disconnects, _client_disconnected must call
    unsubscribe_state, clear _state_subscriptions, and collapse the proxy
    state to None.
    """

    async def _run():
        camera_comm = await make_xmpp_comm("camera", make_module([ICooling]))
        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        await camera_comm.set_state(ICooling, CoolingState(setpoint=-5.0, power=20, enabled=True))

        async with observer_comm.proxy("camera", ICooling) as camera:
            assert await wait_for(lambda: camera.state(ICooling) is not None)

            await camera_comm.close()
            observer_comm._send_event_to_module(ModuleClosedEvent(), "camera")

            assert await wait_for(
                lambda: camera.state(ICooling) is None
            ), "Proxy state did not collapse to None after disconnect"
            assert "camera" not in observer_comm._state_subscriptions

    await asyncio.wait_for(_run(), timeout=60)


async def test_reconnect_resubscribes_with_fresh_proxy(make_xmpp_comm) -> None:
    """
    After disconnect and reconnect, the next proxy() call must produce a fresh
    Proxy with a live subscription to the new session's state.
    """

    async def _run():
        camera_comm = await make_xmpp_comm("camera", make_module([ICooling]))
        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        await camera_comm.set_state(ICooling, CoolingState(setpoint=0.0, power=10, enabled=False))
        async with observer_comm.proxy("camera", ICooling) as camera:
            assert await wait_for(lambda: camera.state(ICooling) is not None)

        await camera_comm.close()
        observer_comm._send_event_to_module(ModuleClosedEvent(), "camera")
        await asyncio.sleep(0.5)

        camera_comm2 = await make_xmpp_comm("camera", make_module([ICooling]))
        await camera_comm2.set_state(ICooling, CoolingState(setpoint=-30.0, power=90, enabled=True))

        await wait_for_peer(observer_comm, "camera")

        async with observer_comm.proxy("camera", ICooling) as camera2:
            assert await wait_for(
                lambda: camera2.state(ICooling) is not None
            ), "No state received from reconnected camera"

    await asyncio.wait_for(_run(), timeout=60)
