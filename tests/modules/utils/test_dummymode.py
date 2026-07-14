from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm import Comm
from pyobs.events import ModeChangedEvent
from pyobs.interfaces import IMode, IMotion, IReady
from pyobs.modules import Module
from pyobs.modules.utils.dummymode import DummyMode


def _state_for(mock: AsyncMock, interface: object) -> object:
    """Find the most recent state object set_state() was called with for the given interface."""
    for call in reversed(mock.await_args_list):
        if call.args[0] is interface:
            return call.args[1]
    raise AssertionError(f"set_state was never called with {interface}")


def _event_of_type(mock: AsyncMock, event_type: type) -> object:
    """Find the send_event() call with an event of the given type."""
    for call in mock.await_args_list:
        if isinstance(call.args[0], event_type):
            return call.args[0]
    raise AssertionError(f"send_event was never called with a {event_type.__name__}")


def make_dummymode(**kwargs) -> DummyMode:
    comm = MagicMock(spec=Comm)
    return DummyMode(comm=comm, **kwargs)


# ── __init__ ────────────────────────────────────────────────────────────────


def test_init_default_modes() -> None:
    dm = make_dummymode()
    assert dm._mode_options == {
        "Size": ["XS", "S", "M", "L", "XL", "XXL"],
        "Speed": ["Slow", "Normal", "Fast"],
        "Movement": ["Rotation", "Linear"],
    }
    assert dm._modes == {"Size": "M", "Speed": "Normal", "Movement": "Linear"}


# ── open ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_publishes_capabilities_and_state(mocker) -> None:
    dm = make_dummymode()
    dm._comm.register_event = AsyncMock()
    dm._comm.set_state = AsyncMock()
    dm._comm.set_capabilities = AsyncMock()
    dm._comm.send_event = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())

    await dm.open()

    dm._comm.set_capabilities.assert_awaited_once()
    interface, caps = dm._comm.set_capabilities.await_args[0]
    assert interface is IMode
    assert caps.modes == dm._mode_options

    mode_state = _state_for(dm._comm.set_state, IMode)
    assert mode_state.modes == dm._modes

    ready_state = _state_for(dm._comm.set_state, IReady)
    assert ready_state.ready is True

    motion_state = _state_for(dm._comm.set_state, IMotion)
    assert motion_state.status.value == "positioned"


# ── set_mode ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_mode_updates_default_group(mocker) -> None:
    dm = make_dummymode()
    dm._comm.send_event = AsyncMock()
    dm._comm.set_state = AsyncMock()
    mocker.patch("pyobs.modules.utils.dummymode.asyncio.wait_for", AsyncMock(side_effect=TimeoutError))

    await dm.set_mode("L")

    assert dm._modes["Size"] == "L"
    event = _event_of_type(dm._comm.send_event, ModeChangedEvent)
    assert (event.group, event.mode) == ("Size", "L")

    mode_state = _state_for(dm._comm.set_state, IMode)
    assert mode_state.modes["Size"] == "L"


@pytest.mark.asyncio
async def test_set_mode_with_explicit_group(mocker) -> None:
    dm = make_dummymode()
    dm._comm.send_event = AsyncMock()
    dm._comm.set_state = AsyncMock()
    mocker.patch("pyobs.modules.utils.dummymode.asyncio.wait_for", AsyncMock(side_effect=TimeoutError))

    await dm.set_mode("Fast", group="Speed")

    assert dm._modes["Speed"] == "Fast"
    event = _event_of_type(dm._comm.send_event, ModeChangedEvent)
    assert (event.group, event.mode) == ("Speed", "Fast")


@pytest.mark.asyncio
async def test_set_mode_raises_for_invalid_group() -> None:
    dm = make_dummymode()

    with pytest.raises(ValueError):
        await dm.set_mode("Whatever", group="NoSuchGroup")


@pytest.mark.asyncio
async def test_set_mode_returns_early_when_closing(mocker) -> None:
    dm = make_dummymode()
    dm._comm.send_event = AsyncMock()
    dm._comm.set_state = AsyncMock()
    # simulate self._closing.wait() completing (module is closing) instead of timing out
    mocker.patch("pyobs.modules.utils.dummymode.asyncio.wait_for", AsyncMock(return_value=None))

    await dm.set_mode("L")

    assert dm._modes["Size"] == "M"  # unchanged
    # motion status still transitions to SLEWING before the closing check, but the
    # mode change itself never happens
    for call in dm._comm.send_event.await_args_list:
        assert not isinstance(call.args[0], ModeChangedEvent)
    for call in dm._comm.set_state.await_args_list:
        assert call.args[0] is not IMode


# ── init/park/stop_motion ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_init_park_stop_motion_are_noops() -> None:
    dm = make_dummymode()
    # should not raise
    await dm.init()
    await dm.park()
    await dm.stop_motion()
