from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pyobs.comm.dummy.dummycomm import DummyComm
from pyobs.events import BadWeatherEvent
from pyobs.interfaces import IExposureTime
from pyobs.utils.parallel import Future


@pytest.fixture
def comm() -> DummyComm:
    return DummyComm()


# ── properties ────────────────────────────────────────────────────────────────


def test_name_is_module(comm: DummyComm) -> None:
    assert comm.name == "module"


def test_clients_is_empty(comm: DummyComm) -> None:
    assert comm.clients == []


# ── interfaces ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_interfaces_returns_empty(comm: DummyComm) -> None:
    assert await comm.get_interfaces("any_client") == []


@pytest.mark.asyncio
async def test_supports_interface_returns_false(comm: DummyComm) -> None:
    assert await comm._supports_interface("any_client", IExposureTime) is False


# ── execute ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_returns_empty_future(comm: DummyComm) -> None:
    result = await comm.execute("client", "method", {"return": None})
    assert isinstance(result, Future)
    assert result.done()


# ── send_event ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_event_dispatches_to_module(comm: DummyComm) -> None:
    handler = AsyncMock(return_value=True)
    await comm.register_event(BadWeatherEvent, handler)

    event = BadWeatherEvent()
    await comm.send_event(event)

    handler.assert_called_once()
    assert handler.call_args[0][0] is event
