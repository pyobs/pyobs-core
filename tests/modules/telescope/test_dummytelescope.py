import asyncio
from unittest.mock import AsyncMock, Mock

import astropy
import pytest
import pytest_mock
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
async def test_move_altaz(mocker: pytest_mock.MockFixture) -> None:
    mocker.patch("pyobs.utils.time.Time.now", return_value=Time("2010-01-01T00:00:00", format="isot"))
    mocker.patch("astropy.coordinates.SkyCoord.transform_to", return_value=SkyCoord(0, 0, unit="deg", frame="icrs"))

    telescope = DummyTelescope()
    telescope.location = EarthLocation(lat=10. * u.degree, lon=10. * u.degree, height=100 * u.meter)
    telescope._move = AsyncMock()

    abort_event = asyncio.Event()
    await telescope._move_altaz(60, 0, abort_event)

    astropy.coordinates.SkyCoord.transform_to.assert_called_once_with("icrs")
    telescope._move.assert_awaited_with(0, 0, abort_event)

@pytest.mark.asyncio
async def test_get_focus() -> None:
    telescope = DummyTelescope()
    telescope._telescope.focus = 10.0

    assert await telescope.get_focus() == 10.0

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
async def test_list_filters() -> None:
    telescope = DummyTelescope()
    telescope._telescope.filters = ["clear"]

    assert await telescope.list_filters() == ["clear"]


@pytest.mark.asyncio
async def test_get_filter() -> None:
    telescope = DummyTelescope()
    telescope._telescope.filter_name = "not_clear"

    assert await telescope.get_filter() == "not_clear"


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
async def test_get_offsets_radec() -> None:
    telescope = DummyTelescope()
    telescope._telescope._offsets = (10.0, 0.0)

    assert await telescope.get_offsets_radec() == (10.0, 0.0)


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


@pytest.mark.asyncio
async def test_get_focus_offset() -> None:
    telescope = DummyTelescope()
    assert await telescope.get_focus_offset() == 0


@pytest.mark.asyncio
async def test_is_ready() -> None:
    telescope = DummyTelescope()
    assert await telescope.is_ready() is True
