import asyncio
import logging
from typing import Any, Tuple, Optional, Dict
from unittest.mock import Mock, AsyncMock

import numpy as np
import pytest
import astropy.units as u
import pytest_mock
from astropy.coordinates import SkyCoord, EarthLocation

import pyobs
from pyobs.comm.dummy import DummyComm
from pyobs.events import MoveAltAzEvent, MoveRaDecEvent
from pyobs.modules.telescope import BaseTelescope
from pyobs.utils.enums import MotionStatus
from pyobs.utils.time import Time


class TestBaseTelescope(BaseTelescope):

    async def _move_radec(self, ra: float, dec: float, abort_event: asyncio.Event) -> None:
        pass

    async def _move_altaz(self, alt: float, az: float, abort_event: asyncio.Event) -> None:
        pass

    async def init(self, **kwargs: Any) -> None:
        pass

    async def park(self, **kwargs: Any) -> None:
        pass

    async def stop_motion(self, device: Optional[str] = None, **kwargs: Any) -> None:
        pass

    async def is_ready(self, **kwargs: Any) -> bool:
        pass

    async def get_altaz(self, **kwargs: Any) -> Tuple[float, float]:
        pass

    async def get_radec(self, **kwargs: Any) -> Tuple[float, float]:
        pass


class MockObserver:
    def moon_altaz(self, time: Time) -> SkyCoord:
        return SkyCoord(alt=60, az=0, unit='deg', frame='altaz')

    def sun_altaz(self, time: Time) -> SkyCoord:
        return SkyCoord(alt=60, az=0, unit='deg', frame='altaz')

    def moon_illumination(self, time: Time) -> float:
        return 0.5

    @property
    def location(self) -> EarthLocation:
        return EarthLocation(lat=10. * u.degree, lon=10. * u.degree, height=100 * u.meter)


@pytest.mark.asyncio
async def test_open(mocker: pytest_mock.MockFixture) -> None:
    mocker.patch("pyobs.mixins.WeatherAwareMixin.open")
    mocker.patch("pyobs.mixins.MotionStatusMixin.open")
    mocker.patch("pyobs.modules.Module.open")

    telescope = TestBaseTelescope()
    await telescope.open()

    pyobs.mixins.WeatherAwareMixin.open.assert_called_once_with(telescope)  # type: ignore
    pyobs.mixins.MotionStatusMixin.open.assert_called_once_with(telescope)  # type: ignore
    pyobs.modules.Module.open.assert_called_once_with(telescope)  # type: ignore


@pytest.mark.asyncio
async def test_update_celestial_headers_no_observer() -> None:
    telescope = TestBaseTelescope()
    celestial_headers = await telescope._calc_celestial_headers()

    assert celestial_headers == {}


def compare_telescope_headers(header: Dict[str, Tuple[Optional[float], str]],
                              moon_alt: Optional[float], moon_frac: Optional[float], moon_dist: Optional[float],
                              sun_alt: Optional[float], sun_dist: Optional[float]) -> None:
    assert header["MOONALT"] == (moon_alt, "Lunar altitude")
    assert header["MOONFRAC"] == (moon_frac, "Fraction of the moon illuminated")
    assert header["MOONDIST"] == (moon_dist, "Lunar distance from target")
    assert header["SUNALT"] == (sun_alt, "Solar altitude")
    assert header["SUNDIST"] == (sun_dist, "Solar Distance from Target")


@pytest.mark.asyncio
async def test_update_celestial_headers_no_altaz() -> None:
    telescope = TestBaseTelescope()
    telescope.observer = MockObserver()

    telescope.get_altaz = AsyncMock(side_effect=Exception)  # type: ignore

    celestial_headers = await telescope._calc_celestial_headers()

    compare_telescope_headers(celestial_headers, 60, 0.5, None, 60, None)


@pytest.mark.asyncio
async def test_update_celestial_headers() -> None:
    telescope = TestBaseTelescope()
    telescope.observer = MockObserver()

    telescope.get_altaz = AsyncMock(return_value=(60, 0))  # type: ignore

    celestial_headers = await telescope._calc_celestial_headers()

    compare_telescope_headers(celestial_headers, 60, 0.5, 0.0, 60, 0.0)


@pytest.mark.asyncio
async def test_get_fits_header_before_no_altaz() -> None:
    telescope = TestBaseTelescope()

    telescope.get_altaz = AsyncMock(side_effect=Exception)  # type: ignore

    assert await telescope.get_fits_header_before() == {}


@pytest.mark.asyncio
async def test_get_fits_header_before_optional_headers() -> None:
    telescope = TestBaseTelescope()
    telescope._fits_headers = {"TEST": (1.0, "TEST")}
    telescope._calc_celestial_headers = AsyncMock(return_value={"CTEST": (1.0, "CTEST")})  # type: ignore

    header = await telescope.get_fits_header_before()

    assert header["TEST"] == (1.0, "TEST")
    assert header["CTEST"] == (1.0, "CTEST")


@pytest.mark.asyncio
async def test_get_fits_header_before_observer() -> None:
    telescope = TestBaseTelescope()
    telescope.observer = MockObserver()

    header = await telescope.get_fits_header_before()

    assert header["LATITUDE"][1] == "Latitude of telescope [deg N]"
    assert header["LONGITUD"][1] == "Longitude of telescope [deg E]"
    assert header["HEIGHT"][1] == "Altitude of telescope [m]"

    np.testing.assert_almost_equal(header["LATITUDE"][0], 10.0)
    np.testing.assert_almost_equal(header["LONGITUD"][0], 10.0)
    np.testing.assert_almost_equal(header["HEIGHT"][0], 100.0)


@pytest.mark.asyncio
async def test_get_fits_header_before_altaz() -> None:
    telescope = TestBaseTelescope()
    telescope.observer = MockObserver()

    telescope.get_radec = AsyncMock(return_value=(60, 0))  # type: ignore
    telescope.get_altaz = AsyncMock(return_value=(60, 0))  # type: ignore

    header = await telescope.get_fits_header_before()

    assert header["TEL-RA"][1] == "Right ascension of telescope [degrees]"
    assert header["TEL-DEC"][1] == "Declination of telescope [degrees]"
    assert header["TEL-ALT"][1] == "Telescope altitude [degrees]"
    assert header["TEL-AZ"][1] == "Telescope azimuth [degrees]"
    assert header["TEL-ZD"][1] == "Telescope zenith distance [degrees]"
    assert header["AIRMASS"][1] == "Airmass of observation start"

    np.testing.assert_almost_equal(header["TEL-RA"][0], 60.0)
    np.testing.assert_almost_equal(header["TEL-DEC"][0], 0.0)

    np.testing.assert_almost_equal(header["TEL-ALT"][0], 60.0)
    np.testing.assert_almost_equal(header["TEL-AZ"][0], 0.0)
    np.testing.assert_almost_equal(header["TEL-ZD"][0], 30.0)
    np.testing.assert_almost_equal(header["AIRMASS"][0], 1.1547005383792517)


@pytest.mark.asyncio
async def test_move_altaz_motion_status() -> None:
    telescope = TestBaseTelescope()
    telescope.get_motion_status = AsyncMock(return_value=MotionStatus.INITIALIZING)  # type: ignore
    telescope._move_altaz = AsyncMock()  # type: ignore

    await telescope.move_altaz(60, 0)
    telescope._move_altaz.assert_not_awaited()


@pytest.mark.asyncio
async def test_move_altaz_min_alt() -> None:
    telescope = TestBaseTelescope()
    telescope.get_motion_status = AsyncMock(return_value=MotionStatus.IDLE)  # type: ignore

    with pytest.raises(ValueError):
        await telescope.move_altaz(0, 0)


@pytest.mark.asyncio
async def test_move_altaz() -> None:
    telescope = TestBaseTelescope()
    telescope.get_motion_status = AsyncMock(return_value=MotionStatus.IDLE)  # type: ignore

    telescope.comm = DummyComm()
    telescope.comm.send_event = AsyncMock()  # type: ignore

    telescope._change_motion_status = AsyncMock()  # type: ignore
    telescope._move_altaz = AsyncMock()  # type: ignore

    telescope._wait_for_motion = AsyncMock()  # type: ignore

    await telescope.move_altaz(60.0, 0.0)

    events, _ = telescope.comm.send_event.call_args
    assert isinstance(events[0], MoveAltAzEvent) and events[0].alt == 60.0 and events[0].az == 0

    status_changes = telescope._change_motion_status.call_args_list
    assert status_changes[0][0][0] == MotionStatus.SLEWING
    assert status_changes[1][0][0] == MotionStatus.POSITIONED

    telescope._move_altaz.assert_awaited_with(60.0, 0.0, abort_event=telescope._abort_move)

    telescope._wait_for_motion.assert_awaited_with(telescope._abort_move)


@pytest.mark.asyncio
async def test_move_altaz_log(caplog: pytest.LogCaptureFixture) -> None:
    telescope = TestBaseTelescope()
    telescope.get_motion_status = AsyncMock(return_value=MotionStatus.IDLE)  # type: ignore

    telescope._change_motion_status = AsyncMock()  # type: ignore # We need to mock this, since this also logs to logging.INFO

    with caplog.at_level(logging.INFO):
        await telescope.move_altaz(60.0, 0.0)

    assert caplog.messages[0] == "Moving telescope to Alt=60.00°, Az=0.00°..."
    assert caplog.messages[1] == "Reached destination"
    assert caplog.messages[2] == "Finished moving telescope."


@pytest.mark.asyncio
async def test_move_radec_motion_status() -> None:
    telescope = TestBaseTelescope()
    telescope.get_motion_status = AsyncMock(return_value=MotionStatus.INITIALIZING)  # type: ignore
    telescope._move_radec = AsyncMock()  # type: ignore

    await telescope.move_radec(60, 0)
    telescope._move_radec.assert_not_awaited()


@pytest.mark.asyncio
async def test_move_radec_no_observer() -> None:
    telescope = TestBaseTelescope()
    telescope.get_motion_status = AsyncMock(return_value=MotionStatus.IDLE)  # type: ignore

    with pytest.raises(ValueError):
        await telescope.move_radec(0, 0)


@pytest.mark.asyncio
async def test_move_radec_min_alt() -> None:
    telescope = TestBaseTelescope()
    telescope.observer = MockObserver()
    telescope.observer.altaz = Mock(return_value=SkyCoord(alt=0.0, az=0.0, unit="deg", frame="altaz"))  # type: ignore

    telescope.get_motion_status = AsyncMock(return_value=MotionStatus.IDLE)  # type: ignore

    with pytest.raises(ValueError):
        await telescope.move_radec(0, 0)


@pytest.mark.asyncio
async def test_move_radec() -> None:
    telescope = TestBaseTelescope()
    telescope.get_motion_status = AsyncMock(return_value=MotionStatus.IDLE)  # type: ignore

    telescope.observer = MockObserver()
    telescope.observer.altaz = Mock(return_value=SkyCoord(alt=60.0, az=0.0, unit="deg", frame="altaz"))  # type: ignore

    telescope.comm = DummyComm()
    telescope.comm.send_event = AsyncMock()  # type: ignore

    telescope._change_motion_status = AsyncMock()  # type: ignore
    telescope._move_radec = AsyncMock()  # type: ignore

    telescope._wait_for_motion = AsyncMock()  # type: ignore

    await telescope.move_radec(60.0, 0.0)

    events, _ = telescope.comm.send_event.call_args
    assert isinstance(events[0], MoveRaDecEvent) and events[0].ra == 60.0 and events[0].dec == 0

    status_changes = telescope._change_motion_status.call_args_list
    assert status_changes[0][0][0] == MotionStatus.SLEWING
    assert status_changes[1][0][0] == MotionStatus.TRACKING

    telescope._move_radec.assert_awaited_with(60.0, 0.0, abort_event=telescope._abort_move)

    telescope._wait_for_motion.assert_awaited_with(telescope._abort_move)


@pytest.mark.asyncio
async def test_move_radec_log(caplog: pytest.LogCaptureFixture) -> None:
    telescope = TestBaseTelescope()
    telescope.get_motion_status = AsyncMock(return_value=MotionStatus.IDLE)  # type: ignore

    telescope.observer = MockObserver()
    telescope.observer.altaz = Mock(return_value=SkyCoord(alt=60.0, az=0.0, unit="deg", frame="altaz"))  # type: ignore

    telescope._change_motion_status = AsyncMock()  # type: ignore # We need to mock this, since this also logs to logging.INFO

    with caplog.at_level(logging.INFO):
        await telescope.move_radec(60.0, 0.0)

    assert caplog.messages[0] == "Moving telescope to RA=04:00:00 (60.00000°), Dec=00:00:00 (0.00000°)..."
    assert caplog.messages[1] == "Reached destination"
    assert caplog.messages[2] == "Finished moving telescope."
