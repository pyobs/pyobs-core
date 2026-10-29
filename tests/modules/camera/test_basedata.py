from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest

from pyobs.events import NewDataEvent, NewImageEvent, NewSpectrumEvent
from pyobs.interfaces import IData, IDataSequence
from pyobs.modules.camera import BaseData


class DummyData(BaseData):
    def __init__(self, **kwargs: Any):
        BaseData.__init__(self, **kwargs)
        self.busy = False

    async def grab_data(self, broadcast: bool = True, **kwargs: Any) -> str:
        filename = "/data/x.dat"
        await self._send_new_data(filename, broadcast)
        return filename

    def _sequence_busy(self) -> bool:
        return self.busy


@pytest.mark.asyncio
async def test_open_declares_only_new_data_event() -> None:
    data = DummyData()
    await data.open()

    assert data.comm._events_sent == {NewDataEvent}
    assert NewImageEvent not in data.comm._events_sent
    assert NewSpectrumEvent not in data.comm._events_sent

    await data.close()


@pytest.mark.asyncio
async def test_open_publishes_idle_sequence_state() -> None:
    data = DummyData()
    data.comm.set_state = AsyncMock()
    await data.open()

    assert data.comm.set_state.call_args[0][0] is IDataSequence


def test_implements_interfaces() -> None:
    data = DummyData()
    assert isinstance(data, IData)
    assert isinstance(data, IDataSequence)


@pytest.mark.asyncio
async def test_send_new_data_sends_event() -> None:
    data = DummyData()
    data.comm.send_event = AsyncMock()

    await data.grab_data()

    data.comm.send_event.assert_called_once()
    event = data.comm.send_event.call_args[0][0]
    assert type(event) is NewDataEvent
    assert event.filename == "/data/x.dat"


@pytest.mark.asyncio
async def test_send_new_data_respects_broadcast_false() -> None:
    data = DummyData()
    data.comm.send_event = AsyncMock()

    await data.grab_data(broadcast=False)

    data.comm.send_event.assert_not_called()


@pytest.mark.asyncio
async def test_grab_sequence_and_abort() -> None:
    data = DummyData()
    data.comm.set_state = AsyncMock()
    gate = asyncio.Event()

    async def slow_grab(broadcast: bool = True, **kwargs: Any) -> str:
        await gate.wait()
        return "f"

    data.grab_data = slow_grab  # type: ignore[method-assign]
    await data.grab_sequence(3)
    assert data._sequence_count_left == 3

    await data.abort()
    gate.set()
    assert data._sequence_task is not None
    await data._sequence_task
    assert data._sequence_count_left == 0


def test_fits_header_options_reach_mixin() -> None:
    data = DummyData(fits_headers={"A": ["b", "c"]}, filenames="/x/{FRAMENUM|string:04d}.fits", fits_header_timeout=2.0)
    assert data._fitsheadermixin_filename_pattern == "/x/{FRAMENUM|string:04d}.fits"
    assert data._fitsheadermixin_header_timeout == 2.0
    assert data._fitsheadermixin_fits_headers["A"] == ["b", "c"]
