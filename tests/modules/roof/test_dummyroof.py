from unittest.mock import AsyncMock, Mock

import pytest

import pyobs
from pyobs.events import RoofOpenedEvent, RoofClosingEvent
from pyobs.modules.roof import DummyRoof
from pyobs.utils.enums import MotionStatus


@pytest.mark.asyncio
async def test_open(mocker) -> None:
    mocker.patch("pyobs.modules.roof.BaseRoof.open")
    roof = DummyRoof()
    roof.comm.register_event = AsyncMock()

    await roof.open()

    pyobs.modules.roof.BaseRoof.open.assert_called_once()

    assert roof.comm.register_event.call_args_list[0][0][0] == RoofOpenedEvent
    assert roof.comm.register_event.call_args_list[1][0][0] == RoofClosingEvent


@pytest.mark.asyncio
async def test_init(mocker) -> None:
    mocker.patch("asyncio.sleep")

    roof = DummyRoof()
    roof._change_motion_status = AsyncMock()
    roof.comm.send_event = Mock()

    await roof.init()

    roof._change_motion_status.assert_awaited_with(MotionStatus.IDLE)
    roof.comm.send_event(RoofOpenedEvent())


@pytest.mark.asyncio
async def test_park(mocker) -> None:
    mocker.patch("asyncio.sleep")

    roof = DummyRoof()
    roof._open_percentage = 100

    roof._change_motion_status = AsyncMock()
    roof.comm.send_event = Mock()

    await roof.park()

    roof._change_motion_status.assert_awaited_with(MotionStatus.PARKED)


@pytest.mark.asyncio
async def test_move_roof_open(mocker) -> None:
    mocker.patch("asyncio.sleep")

    roof = DummyRoof()

    await roof._move_roof(roof._ROOF_OPEN_PERCENTAGE)

    assert roof._open_percentage == 100


@pytest.mark.asyncio
async def test_move_roof_closed(mocker) -> None:
    mocker.patch("asyncio.sleep")

    roof = DummyRoof()

    await roof._move_roof(roof._ROOF_CLOSED_PERCENTAGE)

    assert roof._open_percentage == 0


@pytest.mark.asyncio
async def test_move_roof_abort(mocker) -> None:
    mocker.patch("asyncio.sleep")

    roof = DummyRoof()

    roof._abort_motion.set()
    await roof._move_roof(roof._ROOF_OPEN_PERCENTAGE)

    assert roof._open_percentage == 0


@pytest.mark.asyncio
async def test_move_roof_open(mocker) -> None:
    mocker.patch("asyncio.sleep")

    roof = DummyRoof()

    await roof._move_roof(roof._ROOF_OPEN_PERCENTAGE)

    assert roof._open_percentage == 100


@pytest.mark.asyncio
async def test_stop_motion() -> None:
    roof = DummyRoof()
    roof._change_motion_status = AsyncMock()
    await roof.stop_motion()

    roof._change_motion_status.assert_awaited_with(MotionStatus.IDLE)
