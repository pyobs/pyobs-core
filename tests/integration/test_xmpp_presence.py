"""Integration tests for Phase 2.5 Presence and Discovery.

Requires a live ejabberd server. Uses the same env vars as the other
XMPP integration tests. Run with:

    PYOBS_TEST_XMPP_HOST=localhost PYOBS_TEST_XMPP_DOMAIN=localhost \\
    PYOBS_TEST_XMPP_TLS=1 PYOBS_TEST_XMPP_IGNORE_CERT=1 \\
    pytest -m xmpp tests/integration/test_xmpp_presence.py -v
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm.xmpp.xmppcomm import _CAPABILITY_NS
from pyobs.interfaces import ICooling, IModule
from pyobs.utils.enums import ModuleState

pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.xmpp]


# ---------------------------------------------------------------------------
# helpers (mirrors test_xmpp_state.py)
# ---------------------------------------------------------------------------


def make_module(interfaces: list, label: str = "Test Camera") -> MagicMock:
    m = MagicMock()
    m.interfaces = list({IModule} | set(interfaces))
    m.name = "camera"
    m._label = label
    # get_capabilities returns the real default implementation
    from pyobs.modules.module import Module

    m.get_capabilities = lambda: Module.get_capabilities(m)
    m.get_label = AsyncMock(return_value=label)
    m.get_version = AsyncMock(return_value="2.0.0.dev1")
    return m


async def wait_for(condition, *, timeout: float = 10.0, interval: float = 0.1) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        if condition():
            return True
        await asyncio.sleep(interval)
    return False


async def wait_for_peer(comm, peer: str, *, timeout: float = 15.0) -> None:
    ok = await wait_for(lambda: peer in comm.clients, timeout=timeout)
    assert ok, f"{peer!r} did not appear in client list within {timeout}s"


# ---------------------------------------------------------------------------
# Presence tests
# ---------------------------------------------------------------------------


async def test_presence_ready_visible_to_observer(make_xmpp_comm) -> None:
    """A module in READY state should appear as available to observers."""

    async def _run():
        module = make_module([ICooling])
        camera_comm = await make_xmpp_comm("camera", module)
        await camera_comm.set_presence(ModuleState.READY)

        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        result = observer_comm.get_client_state("camera")
        assert result is not None
        state, error = result
        assert state == ModuleState.READY
        assert error == ""

    await asyncio.wait_for(_run(), timeout=60)


async def test_presence_error_state_delivered(make_xmpp_comm) -> None:
    """ERROR state must arrive as dnd presence with error string in <status>."""

    async def _run():
        module = make_module([ICooling])
        camera_comm = await make_xmpp_comm("camera", module)

        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        await camera_comm.set_presence(ModuleState.ERROR, "sensor overheated")

        ok = await wait_for(
            lambda: (
                observer_comm.get_client_state("camera") is not None
                and observer_comm.get_client_state("camera")[0] == ModuleState.ERROR
            )
        )
        assert ok, "ERROR state not received within timeout"

        state, error = observer_comm.get_client_state("camera")
        assert state == ModuleState.ERROR
        assert "overheated" in error

    await asyncio.wait_for(_run(), timeout=60)


async def test_presence_local_state_delivered(make_xmpp_comm) -> None:
    """LOCAL state must arrive as away presence."""

    async def _run():
        module = make_module([ICooling])
        camera_comm = await make_xmpp_comm("camera", module)

        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        await camera_comm.set_presence(ModuleState.LOCAL)

        ok = await wait_for(
            lambda: (
                observer_comm.get_client_state("camera") is not None
                and observer_comm.get_client_state("camera")[0] == ModuleState.LOCAL
            )
        )
        assert ok, "LOCAL state not received within timeout"

    await asyncio.wait_for(_run(), timeout=60)


async def test_set_state_automatically_updates_presence(make_xmpp_comm) -> None:
    """Module.set_state() must automatically push presence — no explicit call."""

    async def _run():
        from pyobs.modules.module import Module

        module = make_module([ICooling])
        camera_comm = await make_xmpp_comm("camera", module)
        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        # Call set_state on a minimal Module instance wired to camera_comm
        m = Module.__new__(Module)
        m._state = ModuleState.READY
        m._error_string = ""
        m._comm = camera_comm

        await m.set_state(ModuleState.ERROR, "disk full")

        ok = await wait_for(
            lambda: (
                observer_comm.get_client_state("camera") is not None
                and observer_comm.get_client_state("camera")[0] == ModuleState.ERROR
            )
        )
        assert ok, "Presence not updated after set_state()"
        _, error = observer_comm.get_client_state("camera")
        assert "disk full" in error

    await asyncio.wait_for(_run(), timeout=60)


# ---------------------------------------------------------------------------
# Discovery / Capability tests
# ---------------------------------------------------------------------------


async def test_capabilities_in_disco_info(make_xmpp_comm) -> None:
    """disco#info response must contain <capability> elements with version and label."""

    async def _run():
        module = make_module([ICooling], label="My Camera")
        _ = await make_xmpp_comm("camera", module)
        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        # Query disco#info from the camera
        camera_jid = next(jid for jid in observer_comm._online_clients if jid.startswith("camera@"))
        result = await observer_comm.client["xep_0030"].get_info(jid=camera_jid)

        # Extract <capability> elements from response
        caps = {elem.get("name"): elem.text for elem in result.xml.iter(f"{{{_CAPABILITY_NS}}}capability")}

        assert "version" in caps, f"version capability missing; got: {caps}"
        assert "label" in caps, f"label capability missing; got: {caps}"
        assert caps["label"] == "My Camera"
        assert caps["version"] == "2.0.0.dev1"

    await asyncio.wait_for(_run(), timeout=60)


async def test_capability_type_attribute(make_xmpp_comm) -> None:
    """Each <capability> element must carry a type attribute."""

    async def _run():
        module = make_module([ICooling])
        _ = await make_xmpp_comm("camera", module)
        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        camera_jid = next(jid for jid in observer_comm._online_clients if jid.startswith("camera@"))
        result = await observer_comm.client["xep_0030"].get_info(jid=camera_jid)

        for elem in result.xml.iter(f"{{{_CAPABILITY_NS}}}capability"):
            assert elem.get("type"), f"capability {elem.get('name')!r} has no type attribute"
            assert elem.get("type") == "string", f"expected string type, got {elem.get('type')!r}"

    await asyncio.wait_for(_run(), timeout=60)


async def test_custom_capabilities_via_subclass(make_xmpp_comm) -> None:
    """A module that overrides get_capabilities() must expose its extra values."""

    async def _run():
        module = make_module([ICooling])
        # Simulate a subclass that adds full_frame to capabilities
        from pyobs.modules.module import Module

        async def extended_caps():
            base = await Module.get_capabilities(module)
            base["full_frame"] = "0,0,4096,4096"
            return base

        module.get_capabilities = extended_caps

        _ = await make_xmpp_comm("camera", module)
        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        camera_jid = next(jid for jid in observer_comm._online_clients if jid.startswith("camera@"))
        result = await observer_comm.client["xep_0030"].get_info(jid=camera_jid)

        caps = {elem.get("name"): elem.text for elem in result.xml.iter(f"{{{_CAPABILITY_NS}}}capability")}

        assert "full_frame" in caps, f"full_frame capability missing; got: {caps}"
        assert caps["full_frame"] == "0,0,4096,4096"

    await asyncio.wait_for(_run(), timeout=60)
