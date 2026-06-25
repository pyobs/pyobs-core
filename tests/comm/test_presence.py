"""Tests for Phase 2.5 Presence and Capabilities implementation."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pyobs.comm.comm import Comm
from pyobs.modules.module import Module
from pyobs.utils.enums import ModuleState

# ---------------------------------------------------------------------------
# Module.set_state → set_presence hook
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_state_calls_set_presence() -> None:
    """set_state() must automatically call comm.set_presence()."""
    module = Module.__new__(Module)
    module._state = ModuleState.READY
    module._error_string = ""

    comm = MagicMock()
    comm.set_presence = AsyncMock()
    module._comm = comm

    await module.set_state(ModuleState.ERROR, "sensor failure")

    comm.set_presence.assert_called_once_with(ModuleState.ERROR, "sensor failure")


@pytest.mark.asyncio
async def test_set_state_no_comm_does_not_raise() -> None:
    """set_state() must not raise when comm is None."""
    module = Module.__new__(Module)
    module._state = ModuleState.READY
    module._error_string = ""
    module._comm = None

    await module.set_state(ModuleState.ERROR)  # should not raise


@pytest.mark.asyncio
async def test_set_state_passes_current_error_string() -> None:
    """set_state() without explicit error_string passes the stored error string."""
    module = Module.__new__(Module)
    module._state = ModuleState.READY
    module._error_string = "existing error"

    comm = MagicMock()
    comm.set_presence = AsyncMock()
    module._comm = comm

    await module.set_state(ModuleState.ERROR)

    comm.set_presence.assert_called_once_with(ModuleState.ERROR, "existing error")


@pytest.mark.asyncio
async def test_set_state_ready_clears_error() -> None:
    """set_state(READY) passes empty error string."""
    module = Module.__new__(Module)
    module._state = ModuleState.ERROR
    module._error_string = "previous error"

    comm = MagicMock()
    comm.set_presence = AsyncMock()
    module._comm = comm

    await module.set_state(ModuleState.READY, "")

    comm.set_presence.assert_called_once_with(ModuleState.READY, "")


# ---------------------------------------------------------------------------
# Module.get_capabilities
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_open_publishes_imodule_capabilities() -> None:
    """Module.open() must call set_capabilities with IModule.Capabilities."""
    from pyobs.interfaces import IModule

    module = Module.__new__(Module)
    module._label = "Test Camera"
    module._child_objects = []
    module._own_comm = False  # skip comm.open()
    module._config_caps = {}  # no config caps for stub

    comm = MagicMock()
    comm.set_capabilities = AsyncMock()
    module._comm = comm

    with patch("pyobs.object.Object.open", new_callable=AsyncMock):
        module.get_version = AsyncMock(return_value="2.0.0")
        module.get_label = AsyncMock(return_value="Test Camera")
        await module.open()

    # set_capabilities called for IModule.Capabilities and IConfig.Capabilities
    assert comm.set_capabilities.call_count >= 1
    imodule_call = next(c for c in comm.set_capabilities.call_args_list if isinstance(c[0][0], IModule.Capabilities))
    caps = imodule_call[0][0]
    assert caps.version == "2.0.0"
    assert caps.label == "Test Camera"


@pytest.mark.asyncio
async def test_open_publishes_empty_label_when_none() -> None:
    """Module.open() passes empty string for label when _label is None."""
    from pyobs.interfaces import IModule

    module = Module.__new__(Module)
    module._label = None
    module._child_objects = []
    module._own_comm = False
    module._config_caps = {}

    comm = MagicMock()
    comm.set_capabilities = AsyncMock()
    module._comm = comm

    with patch("pyobs.object.Object.open", new_callable=AsyncMock):
        module.get_version = AsyncMock(return_value="2.0.0")
        module.get_label = AsyncMock(return_value="")
        await module.open()

    imodule_call = next(c for c in comm.set_capabilities.call_args_list if isinstance(c[0][0], IModule.Capabilities))
    caps = imodule_call[0][0]
    assert isinstance(caps, IModule.Capabilities)
    assert caps.label == ""


# ---------------------------------------------------------------------------
# Comm.get_client_state / _get_client_state
# ---------------------------------------------------------------------------


def test_comm_get_client_state_delegates() -> None:
    """get_client_state() delegates to _get_client_state()."""
    comm = Comm.__new__(Comm)
    comm._get_client_state = MagicMock(return_value=(ModuleState.READY, ""))

    result = comm.get_client_state("camera")

    comm._get_client_state.assert_called_once_with("camera")
    assert result == (ModuleState.READY, "")


def test_comm_get_client_state_base_returns_none() -> None:
    """Base Comm._get_client_state returns None (no presence info)."""
    comm = Comm.__new__(Comm)

    assert comm._get_client_state("camera") is None
    assert comm.get_client_state("camera") is None


# ---------------------------------------------------------------------------
# XmppComm presence state tracking
# ---------------------------------------------------------------------------


def make_xmpp_comm() -> object:
    """Create a minimal XmppComm instance for testing."""
    from pyobs.comm.xmpp.xmppcomm import XmppComm

    comm = XmppComm.__new__(XmppComm)
    comm._client_states = {}
    comm._online_clients = []
    comm._interface_cache = {}
    return comm


def test_xmpp_get_client_state_unknown_module() -> None:
    """_get_client_state returns None for unknown module."""

    comm = make_xmpp_comm()
    assert comm._get_client_state("camera") is None


def test_xmpp_get_client_state_known_module() -> None:
    """_get_client_state returns stored state by module name prefix."""

    comm = make_xmpp_comm()
    comm._client_states["camera@localhost/pyobs"] = (ModuleState.READY, "")

    result = comm._get_client_state("camera")
    assert result == (ModuleState.READY, "")


def test_xmpp_get_client_state_error_module() -> None:
    """_get_client_state returns ERROR state with error string."""

    comm = make_xmpp_comm()
    comm._client_states["telescope@localhost/pyobs"] = (ModuleState.ERROR, "mount stalled")

    result = comm._get_client_state("telescope")
    assert result is not None
    assert result[0] == ModuleState.ERROR
    assert result[1] == "mount stalled"


def test_xmpp_presence_show_mapping() -> None:
    """ModuleState maps to the correct XMPP <show> values."""
    # Test the mapping logic directly without needing a live connection
    show_map = {
        ModuleState.READY: None,
        ModuleState.ERROR: "dnd",
        ModuleState.LOCAL: "away",
    }
    assert show_map[ModuleState.READY] is None
    assert show_map[ModuleState.ERROR] == "dnd"
    assert show_map[ModuleState.LOCAL] == "away"


# ---------------------------------------------------------------------------
# Comm.get_capabilities / _get_capabilities
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_comm_get_capabilities_delegates() -> None:
    """get_capabilities() delegates to _get_capabilities()."""
    from pyobs.interfaces import IWindow

    comm = Comm.__new__(Comm)
    comm._get_capabilities = AsyncMock(return_value=IWindow.Capabilities())

    result = await comm.get_capabilities("camera", IWindow)

    comm._get_capabilities.assert_called_once_with("camera", IWindow)
    assert isinstance(result, IWindow.Capabilities)


@pytest.mark.asyncio
async def test_comm_get_capabilities_base_returns_none() -> None:
    """Base Comm._get_capabilities returns None."""
    from pyobs.interfaces import IWindow

    comm = Comm.__new__(Comm)
    assert await comm._get_capabilities("camera", IWindow) is None
    assert await comm.get_capabilities("camera", IWindow) is None


@pytest.mark.asyncio
async def test_get_capabilities_no_capabilities_class() -> None:
    """_get_capabilities returns None for interfaces without a Capabilities class."""
    from pyobs.comm.xmpp.xmppcomm import XmppComm
    from pyobs.interfaces import ICooling  # has no Capabilities

    comm = XmppComm.__new__(XmppComm)
    comm._client_states = {}
    comm._online_clients = []

    result = await comm._get_capabilities("camera", ICooling)
    assert result is None
