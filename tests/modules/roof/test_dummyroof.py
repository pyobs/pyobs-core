from unittest.mock import AsyncMock, Mock

import pytest

from pyobs.events import RoofOpenedEvent
from pyobs.modules.roof import DummyRoof
from pyobs.utils.enums import MotionStatus


@pytest.mark.asyncio
async def test_init(mocker):
    mocker.patch("asyncio.sleep")

    roof = DummyRoof()
    roof._change_motion_status = AsyncMock()
    roof.comm.send_event = Mock()

    await roof.init()

    assert roof.open_percentage == 100
    roof._change_motion_status.assert_awaited_with(MotionStatus.IDLE)
    roof.comm.send_event(RoofOpenedEvent())


@pytest.mark.asyncio
async def test_park(mocker):
    mocker.patch("asyncio.sleep")

    roof = DummyRoof()
    roof.open_percentage = 100

    roof._change_motion_status = AsyncMock()
    roof.comm.send_event = Mock()

    await roof.park()

    assert roof.open_percentage == 0
    roof._change_motion_status.assert_awaited_with(MotionStatus.PARKED)


@pytest.mark.asyncio
async def test_stop_motion():
    roof = DummyRoof()
    roof._change_motion_status = AsyncMock()
    await roof.stop_motion()

    roof._change_motion_status.assert_awaited_with(MotionStatus.IDLE)