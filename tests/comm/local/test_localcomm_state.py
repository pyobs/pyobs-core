"""Tests for LocalComm state, capabilities, and presence."""

from __future__ import annotations

import pytest

from pyobs.comm.local.localcomm import LocalComm
from pyobs.comm.local.localnetwork import LocalNetwork
from pyobs.interfaces import ICooling, IModule, IWindow
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

    state = ICooling.State(setpoint=-20.0, power=65, enabled=True)
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
    state = ICooling.State(setpoint=-10.0, power=80, enabled=True)
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
async def test_iwindow_capabilities_roundtrip() -> None:
    """IWindow.Capabilities round-trips through LocalComm."""
    camera = LocalComm("camera")
    observer = LocalComm("observer")

    caps = IWindow.Capabilities(full_frame=IWindow.State(x=0, y=0, width=4096, height=4096))
    await camera._set_capabilities(IWindow, caps)

    result = await observer._get_capabilities("camera", IWindow)
    assert result is not None
    assert result.full_frame.width == 4096
    assert result.full_frame.height == 4096
