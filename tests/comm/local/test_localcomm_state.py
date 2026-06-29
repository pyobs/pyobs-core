"""Tests for LocalComm state, capabilities, and presence."""

from __future__ import annotations

import pytest

from pyobs.comm.local.localcomm import LocalComm
from pyobs.comm.local.localnetwork import LocalNetwork
from pyobs.interfaces import CoolingState, ICooling, IModule, IWindow, WindowState
from pyobs.utils.enums import ModuleState


@pytest.fixture(autouse=True)
def reset_network():
    """Reset LocalNetwork singleton before each test."""
    LocalNetwork._instance = None
    yield
    LocalNetwork._instance = None


@pytest.mark.asyncio
async def test_set_and_get_state() -> None:
    """set_state publishes to subscribers immediately."""
    camera = LocalComm("camera")
    observer = LocalComm("observer")

    received = []
    await observer._subscribe_state("camera", ICooling, received.append)

    state = CoolingState(setpoint=-20.0, power=65, enabled=True)
    await camera._set_state(ICooling, state)

    assert len(received) == 1
    assert received[0].setpoint == -20.0
    assert received[0].enabled is True


@pytest.mark.asyncio
async def test_subscribe_delivers_current_value() -> None:
    """Subscribing after state published delivers current value immediately."""
    camera = LocalComm("camera")
    observer = LocalComm("observer")

    # Camera publishes first
    state = CoolingState(setpoint=-10.0, power=80, enabled=True)
    await camera._set_state(ICooling, state)

    # Observer subscribes later — should get current value
    received = []
    await observer._subscribe_state("camera", ICooling, received.append)

    assert len(received) == 1
    assert received[0].setpoint == -10.0


@pytest.mark.asyncio
async def test_set_and_get_capabilities() -> None:
    """set_capabilities stores and get_capabilities retrieves."""
    camera = LocalComm("camera")
    observer = LocalComm("observer")

    caps = IModule.Capabilities(version="2.0.0", label="Test Camera")
    await camera._set_capabilities(IModule, caps)

    result = await observer._get_capabilities("camera", IModule)
    assert result is not None
    assert isinstance(result, IModule.Capabilities)
    assert result.version == "2.0.0"
    assert result.label == "Test Camera"


@pytest.mark.asyncio
async def test_get_capabilities_unknown_interface() -> None:
    """get_capabilities returns None for interface without Capabilities class."""
    LocalComm("camera")
    observer = LocalComm("observer")

    result = await observer._get_capabilities("camera", ICooling)
    assert result is None


@pytest.mark.asyncio
async def test_set_and_get_presence() -> None:
    """set_presence stores and get_client_state retrieves."""
    camera = LocalComm("camera")
    observer = LocalComm("observer")

    await camera._set_presence(ModuleState.ERROR, "sensor failure")

    result = observer._get_client_state("camera")
    assert result is not None
    assert result[0] == ModuleState.ERROR
    assert result[1] == "sensor failure"


@pytest.mark.asyncio
async def test_presence_default_ready() -> None:
    """Default presence is READY with no error string."""
    LocalComm("camera")
    observer = LocalComm("observer")

    result = observer._get_client_state("camera")
    assert result == (ModuleState.READY, "")


@pytest.mark.asyncio
async def test_subscribe_presence_delivers_current() -> None:
    """subscribe_presence fires callback immediately with the current presence state."""
    camera = LocalComm("camera")
    observer = LocalComm("observer")

    await camera._set_presence(ModuleState.ERROR, "sensor failure")

    received: list[tuple[ModuleState, str]] = []
    await observer.subscribe_presence("camera", lambda s, e: received.append((s, e)))

    assert received == [(ModuleState.ERROR, "sensor failure")]


@pytest.mark.asyncio
async def test_subscribe_presence_called_on_change() -> None:
    """subscribe_presence callback is called whenever presence changes."""
    camera = LocalComm("camera")
    observer = LocalComm("observer")

    received: list[tuple[ModuleState, str]] = []
    await observer.subscribe_presence("camera", lambda s, e: received.append((s, e)))
    received.clear()  # discard the immediate delivery

    await camera._set_presence(ModuleState.ERROR, "disk full")

    assert received == [(ModuleState.ERROR, "disk full")]


@pytest.mark.asyncio
async def test_subscribe_presence_multiple_callbacks() -> None:
    """All registered callbacks receive each presence update."""
    camera = LocalComm("camera")
    obs1 = LocalComm("obs1")
    obs2 = LocalComm("obs2")

    r1: list[tuple[ModuleState, str]] = []
    r2: list[tuple[ModuleState, str]] = []
    await obs1.subscribe_presence("camera", lambda s, e: r1.append((s, e)))
    await obs2.subscribe_presence("camera", lambda s, e: r2.append((s, e)))
    r1.clear()
    r2.clear()

    await camera._set_presence(ModuleState.LOCAL)

    assert (ModuleState.LOCAL, "") in r1
    assert (ModuleState.LOCAL, "") in r2


@pytest.mark.asyncio
async def test_iwindow_capabilities_roundtrip() -> None:
    """IWindow.Capabilities round-trips through LocalComm."""
    camera = LocalComm("camera")
    observer = LocalComm("observer")

    caps = IWindow.Capabilities(full_frame=WindowState(x=0, y=0, width=4096, height=4096))
    await camera._set_capabilities(IWindow, caps)

    result = await observer._get_capabilities("camera", IWindow)
    assert result is not None
    assert result.full_frame.width == 4096
    assert result.full_frame.height == 4096
