import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from astropy.coordinates import EarthLocation, SkyCoord

import astropy.units as u
from pyobs.comm.dummy import DummyComm
from pyobs.events import FilterChangedEvent, OffsetsRaDecEvent
from pyobs.modules.telescope import DummyTelescope, BaseTelescope
from pyobs.utils.enums import MotionStatus
from pyobs.utils.time import Time


@pytest.mark.asyncio
async def test_open() -> None:
    BaseTelescope.open = AsyncMock()

    telescope = DummyTelescope()
    telescope._change_motion_status = AsyncMock()
    telescope.comm = DummyComm()
    telescope.comm.register_event = AsyncMock()

    await telescope.open()

    events = telescope.comm.register_event.call_args_list
    assert events[0][0][0] == FilterChangedEvent
    assert events[1][0][0] == OffsetsRaDecEvent

    telescope._change_motion_status.assert_awaited_once_with(MotionStatus.IDLE)


@pytest.mark.asyncio
async def test_move_radec() -> None:
    telescope = DummyTelescope()
    telescope._move = AsyncMock()

    abort_event = asyncio.Event()
    await telescope._move_radec(60, 0, abort_event)

    telescope._move.assert_awaited_once_with(60, 0, abort_event)


@pytest.mark.asyncio
async def test_move_altaz(mocker) -> None:
    mocker.patch("pyobs.utils.time.Time.now", return_value=Time("2010-01-01T00:00:00", format="isot"))

    telescope = DummyTelescope()
    telescope.location = EarthLocation(lat=10. * u.degree, lon=10. * u.degree, height=100 * u.meter)
    telescope._move = AsyncMock()

    abort_event = asyncio.Event()
    await telescope._move_altaz(60, 0, abort_event)

    telescope._move.assert_awaited_with(110.35706910444917, 40.020387331332806, abort_event)


@pytest.mark.asyncio
async def test_set_focus_invalid() -> None:
    telescope = DummyTelescope()

    with pytest.raises(ValueError):
        await telescope.set_focus(-1)

    with pytest.raises(ValueError):
        await telescope.set_focus(101)


@pytest.mark.asyncio
async def test_set_focus(mocker) -> None:
    mocker.patch("asyncio.sleep")
    telescope = DummyTelescope()

    await telescope.set_focus(60.0)
    assert telescope._telescope.focus == 60.0


@pytest.mark.asyncio
async def test_stop_focus(mocker) -> None:
    mocker.patch("asyncio.sleep")
    telescope = DummyTelescope()
    telescope._telescope.focus = 10.0
    await telescope._step_focus(10.0)

    assert telescope._telescope.focus == 20.0
    asyncio.sleep.assert_called_once_with(0.01)


@pytest.mark.asyncio
async def test_stop_focus_abord(mocker) -> None:
    mocker.patch("asyncio.sleep")
    telescope = DummyTelescope()
    telescope._telescope.focus = 10.0
    telescope._abort_focus.set()
    with pytest.raises(InterruptedError):
        await telescope._step_focus(10.0)


@pytest.mark.asyncio
async def test_set_filter_invalid_filter() -> None:
    telescope = DummyTelescope()

    telescope._telescope.filters = ["clear"]

    with pytest.raises(ValueError):
        await telescope.set_filter("B")


@pytest.mark.asyncio
async def test_set_filter(mocker) -> None:
    mocker.patch("asyncio.sleep")
    telescope = DummyTelescope()

    telescope._telescope.filters = ["clear", "B"]
    telescope._telescope.filter_name = "clear"

    await telescope.set_filter("B")

    assert telescope._telescope.filter_name == "B"


@pytest.mark.asyncio
async def test_init(mocker) -> None:
    mocker.patch("asyncio.sleep")
    telescope = DummyTelescope()
    telescope._change_motion_status = AsyncMock()

    await telescope.init()

    status = telescope._change_motion_status.call_args_list
    assert status[0][0][0] == MotionStatus.INITIALIZING
    assert status[1][0][0] == MotionStatus.IDLE


@pytest.mark.asyncio
async def test_park(mocker) -> None:
    mocker.patch("asyncio.sleep")
    telescope = DummyTelescope()
    telescope._change_motion_status = AsyncMock()

    await telescope.park()

    status = telescope._change_motion_status.call_args_list
    assert status[0][0][0] == MotionStatus.PARKING
    assert status[1][0][0] == MotionStatus.PARKED


@pytest.mark.asyncio
async def test_set_offsets_radec() -> None:
    telescope = DummyTelescope()
    telescope.comm = DummyComm()
    telescope.comm.send_event = AsyncMock()
    telescope._telescope.set_offsets = Mock()

    await telescope.set_offsets_radec(1, 1)

    telescope._telescope.set_offsets.assert_called_once_with(1, 1)
    event, _ = telescope.comm.send_event.call_args
    assert isinstance(event[0], OffsetsRaDecEvent) and event[0].ra == 1 and event[0].dec == 1


@pytest.mark.asyncio
async def test_get_fits_header_before() -> None:
    BaseTelescope._get_fits_header_before = AsyncMock(return_value={})

    telescope = DummyTelescope()
    telescope._telescope.focus = 10.0

    result = await telescope.get_fits_header_before(sender="sender")
    assert result["TEL-FOCU"] == (10.0, "Focus position [mm]")
