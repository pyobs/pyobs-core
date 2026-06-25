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

from pyobs.interfaces import ICooling, IModule, IWindow
from pyobs.utils.enums import ModuleState

pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.xmpp]

_CAPABILITIES_NS_IMODULE = f"urn:pyobs:capabilities:IModule:{IModule.version}"
_CAPABILITIES_NS_IWINDOW = f"urn:pyobs:capabilities:IWindow:{IWindow.version}"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def make_module(interfaces: list, label: str = "Test Camera") -> MagicMock:
    m = MagicMock()
    m.interfaces = list({IModule} | set(interfaces))
    m.name = "camera"
    m._label = label
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


def get_capabilities_from_disco(result_xml, namespace: str) -> dict[str, str]:
    """Extract field name → text from a <capabilities> element in a disco#info result."""

    caps = {}
    for cap_elem in result_xml.iter(f"{{{namespace}}}capabilities"):
        for child in cap_elem:
            tag = child.tag.split("}")[-1]
            # value is wrapped in a vocabulary element e.g. <string>foo</string>
            value_elem = list(child)
            if value_elem:
                caps[tag] = value_elem[0].text
            else:
                caps[tag] = child.text
    return caps


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


async def test_imodule_capabilities_in_disco_info(make_xmpp_comm) -> None:
    """disco#info must contain IModule.Capabilities with version and label."""

    async def _run():
        module = make_module([ICooling], label="My Camera")
        camera_comm = await make_xmpp_comm("camera", module)

        # publish capabilities explicitly (normally done by Module.open())
        await camera_comm.set_capabilities(IModule.Capabilities(version="2.0.0.dev1", label="My Camera"))

        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        camera_jid = next(jid for jid in observer_comm._online_clients if jid.startswith("camera@"))
        result = await observer_comm.client["xep_0030"].get_info(jid=camera_jid)
        caps = get_capabilities_from_disco(result.xml, _CAPABILITIES_NS_IMODULE)

        assert "version" in caps, f"version missing; got: {caps}"
        assert "label" in caps, f"label missing; got: {caps}"
        assert caps["label"] == "My Camera"
        assert caps["version"] == "2.0.0.dev1"

    await asyncio.wait_for(_run(), timeout=60)


async def test_iwindow_capabilities_in_disco_info(make_xmpp_comm) -> None:
    """disco#info must contain IWindow.Capabilities with full_frame fields."""

    async def _run():
        module = make_module([ICooling, IWindow])
        camera_comm = await make_xmpp_comm("camera", module)

        await camera_comm.set_capabilities(IModule.Capabilities(version="2.0.0.dev1", label="My Camera"))
        await camera_comm.set_capabilities(
            IWindow.Capabilities(
                full_frame_x=0,
                full_frame_y=0,
                full_frame_width=4096,
                full_frame_height=4096,
            )
        )

        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        camera_jid = next(jid for jid in observer_comm._online_clients if jid.startswith("camera@"))
        result = await observer_comm.client["xep_0030"].get_info(jid=camera_jid)
        caps = get_capabilities_from_disco(result.xml, _CAPABILITIES_NS_IWINDOW)

        assert "full_frame_width" in caps, f"full_frame_width missing; got: {caps}"
        assert caps["full_frame_width"] == "4096"
        assert caps["full_frame_height"] == "4096"

    await asyncio.wait_for(_run(), timeout=60)


async def test_multiple_interface_capabilities(make_xmpp_comm) -> None:
    """Multiple set_capabilities() calls must all appear in disco#info."""

    async def _run():
        module = make_module([ICooling, IWindow])
        camera_comm = await make_xmpp_comm("camera", module)

        await camera_comm.set_capabilities(IModule.Capabilities(version="2.0.0.dev1", label="Multi Cap Camera"))
        await camera_comm.set_capabilities(
            IWindow.Capabilities(
                full_frame_x=0,
                full_frame_y=0,
                full_frame_width=512,
                full_frame_height=512,
            )
        )

        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        camera_jid = next(jid for jid in observer_comm._online_clients if jid.startswith("camera@"))
        result = await observer_comm.client["xep_0030"].get_info(jid=camera_jid)

        imodule_caps = get_capabilities_from_disco(result.xml, _CAPABILITIES_NS_IMODULE)
        iwindow_caps = get_capabilities_from_disco(result.xml, _CAPABILITIES_NS_IWINDOW)

        assert "version" in imodule_caps
        assert "full_frame_width" in iwindow_caps

    await asyncio.wait_for(_run(), timeout=60)


async def test_get_capabilities_api(make_xmpp_comm) -> None:
    """comm.get_capabilities() must return a deserialized Capabilities dataclass."""

    async def _run():
        module = make_module([ICooling, IWindow])
        camera_comm = await make_xmpp_comm("camera", module)

        await camera_comm.set_capabilities(IModule.Capabilities(version="2.0.0.dev1", label="My Camera"))
        await camera_comm.set_capabilities(
            IWindow.Capabilities(
                full_frame_x=0,
                full_frame_y=0,
                full_frame_width=4096,
                full_frame_height=4096,
            )
        )

        observer_comm = await make_xmpp_comm("observer")
        await wait_for_peer(observer_comm, "camera")

        # Fetch IModule capabilities
        imodule_caps = await observer_comm.get_capabilities("camera", IModule)
        assert imodule_caps is not None
        assert isinstance(imodule_caps, IModule.Capabilities)
        assert imodule_caps.version == "2.0.0.dev1"
        assert imodule_caps.label == "My Camera"

        # Fetch IWindow capabilities
        iwindow_caps = await observer_comm.get_capabilities("camera", IWindow)
        assert iwindow_caps is not None
        assert isinstance(iwindow_caps, IWindow.Capabilities)
        assert iwindow_caps.full_frame_width == 4096
        assert iwindow_caps.full_frame_height == 4096

    await asyncio.wait_for(_run(), timeout=60)
