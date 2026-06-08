from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm.local.localcomm import LocalComm
from pyobs.comm.local.localnetwork import LocalNetwork
from pyobs.events import BadWeatherEvent, GoodWeatherEvent
from pyobs.interfaces import IExposureTime


@pytest.fixture(autouse=True)
def reset_network() -> None:
    """Reset LocalNetwork singleton between tests."""
    LocalNetwork._instance = None
    yield
    LocalNetwork._instance = None


def make_comm(name: str) -> LocalComm:
    return LocalComm(name=name)


# ── properties ────────────────────────────────────────────────────────────────


def test_name(reset_network) -> None:
    comm = make_comm("camera")
    assert comm.name == "camera"


def test_clients_includes_self(reset_network) -> None:
    comm = make_comm("camera")
    assert "camera" in comm.clients


def test_clients_includes_all_connected(reset_network) -> None:
    c1 = make_comm("camera")  # noqa: F841
    c2 = make_comm("telescope")  # noqa: F841
    assert "camera" in c1.clients
    assert "telescope" in c1.clients


# ── get_interfaces ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_interfaces_no_module(reset_network) -> None:
    """get_interfaces returns [] when the remote client has no module."""
    comm = make_comm("camera")
    result = await comm.get_interfaces("camera")
    assert result == []


@pytest.mark.asyncio
async def test_get_interfaces_with_module(reset_network) -> None:
    comm = make_comm("camera")
    module = MagicMock()
    module.interfaces = [IExposureTime]
    comm.module = module

    result = await comm.get_interfaces("camera")
    assert IExposureTime in result


# ── _supports_interface ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_supports_interface_true(reset_network) -> None:
    comm = make_comm("camera")
    module = MagicMock()
    module.interfaces = [IExposureTime]
    comm.module = module

    assert await comm._supports_interface("camera", IExposureTime) is True


@pytest.mark.asyncio
async def test_supports_interface_false(reset_network) -> None:
    comm = make_comm("camera")
    module = MagicMock()
    module.interfaces = []
    comm.module = module

    assert await comm._supports_interface("camera", IExposureTime) is False


# ── execute ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_calls_remote_module(reset_network) -> None:
    c1 = make_comm("caller")
    c2 = make_comm("camera")

    module = MagicMock()
    module.execute = AsyncMock(return_value=30.0)
    c2.module = module

    annotation = {"return": None}
    result = await c1.execute("camera", "get_exposure_time", annotation)

    module.execute.assert_called_once_with("get_exposure_time", sender="caller")
    assert result == 30.0


@pytest.mark.asyncio
async def test_execute_raises_when_no_module(reset_network) -> None:
    c1 = make_comm("caller")  # noqa: F841
    c2 = make_comm("camera")  # noqa: F841

    with pytest.raises(ValueError):
        await c1.execute("camera", "abort", {"return": None})


# ── send_event ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_event_dispatches_to_all_clients(reset_network) -> None:
    c1 = make_comm("sender")
    c2 = make_comm("receiver")

    handler = AsyncMock(return_value=True)
    await c2.register_event(BadWeatherEvent, handler)

    event = BadWeatherEvent()
    await c1.send_event(event)

    handler.assert_called_once()
    assert handler.call_args[0][0] is event


@pytest.mark.asyncio
async def test_send_event_dispatches_to_sender_too(reset_network) -> None:
    """Sender also receives its own events."""
    comm = make_comm("solo")

    handler = AsyncMock(return_value=True)
    await comm.register_event(GoodWeatherEvent, handler)

    event = GoodWeatherEvent()
    await comm.send_event(event)

    handler.assert_called_once()
