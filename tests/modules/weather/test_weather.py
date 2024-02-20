import asyncio
import logging
from unittest.mock import AsyncMock, Mock

import pytest

import pyobs
from pyobs.comm.dummy import DummyComm
from pyobs.events import GoodWeatherEvent, BadWeatherEvent
from pyobs.modules import Module
from pyobs.modules.weather import Weather
from pyobs.utils.enums import WeatherSensors
from pyobs.utils.time import Time


@pytest.mark.asyncio
async def test_open() -> None:
    weather = Weather("")
    weather.comm = DummyComm()
    weather.comm.register_event = AsyncMock()

    Module.open = AsyncMock()

    await weather.open()

    weather.comm.register_event.assert_called()

    assert weather.comm.register_event.await_args_list[0][0][0] == BadWeatherEvent
    assert weather.comm.register_event.await_args_list[1][0][0] == GoodWeatherEvent


@pytest.mark.asyncio
async def test_start() -> None:
    weather = Weather("")
    weather.comm = DummyComm()
    weather.comm.send_event = AsyncMock()

    weather._active = False
    weather._is_good = False

    await weather.start()

    assert weather._active == True
    assert isinstance(weather.comm.send_event.await_args[0][0], BadWeatherEvent)


@pytest.mark.asyncio
async def test_stop() -> None:
    weather = Weather("")
    await weather.stop()
    assert weather._active == False


@pytest.mark.asyncio
async def test_is_running() -> None:
    weather = Weather("")
    await weather.is_running() == False

    weather._active = True
    await weather.is_running() == True


@pytest.mark.asyncio
async def test_get_sensor_value_invalid_request():
    weather = Weather("example.com/")

    weather._api.get_sensor_value = AsyncMock(side_effect=ValueError)

    with pytest.raises(ValueError):
        await weather.get_sensor_value("test", WeatherSensors.RAIN)

    weather._api.get_sensor_value.assert_called_once_with("test", WeatherSensors.RAIN)


@pytest.mark.asyncio
async def test_get_sensor_value_invalid_response():
    weather = Weather("example.com/")

    weather._api.get_sensor_value = AsyncMock(return_value={})
    with pytest.raises(ValueError):
        await weather.get_sensor_value("test", WeatherSensors.RAIN)


@pytest.mark.asyncio
async def test_get_sensor_value():
    weather = Weather("example.com/")

    weather._api.get_sensor_value = AsyncMock(return_value={"time": 1, "value": 2})
    assert await weather.get_sensor_value("test", WeatherSensors.RAIN) == (1, 2)


@pytest.mark.asyncio
async def test_get_fits_header_before_invalid(caplog) -> None:
    weather = Weather("")

    with caplog.at_level(logging.ERROR):
        assert await weather.get_fits_header_before() == {}


@pytest.mark.asyncio
async def test_get_fits_header_before(caplog) -> None:
    weather = Weather("")
    weather._weather.status["sensors"] = {"rain": {"value": 1}}

    header = await weather.get_fits_header_before()
    assert header["WS-PREC"] == (True, "Ambient precipitation [0/1]")


@pytest.mark.asyncio
async def test_loop_valid(mocker) -> None:
    weather = Weather("")
    weather._update = AsyncMock()

    mocker.patch("asyncio.sleep")

    await weather._loop()

    asyncio.sleep.assert_called_once_with(5)


@pytest.mark.asyncio
async def test_loop_invalid(mocker) -> None:
    weather = Weather("")
    weather._update = AsyncMock(side_effect=ValueError)

    mocker.patch("asyncio.sleep")

    await weather._loop()

    asyncio.sleep.assert_called_once_with(60)

@pytest.mark.asyncio
async def test_update_invalid_url(caplog) -> None:
    weather = Weather("example.com/")
    weather._api.get_current_status = AsyncMock(side_effect=ValueError("Could not connect to weather station."))

    with caplog.at_level(logging.WARN):
        await weather._update()

    assert weather._weather.is_good == False
    assert caplog.messages[0] == "Request failed: Could not connect to weather station."

    weather._api.get_current_status.assert_called_once_with()


@pytest.mark.asyncio
async def test_update_invalid_response(caplog) -> None:
    weather = Weather("example.com/")

    weather._api.get_current_status = AsyncMock(return_value={})

    with caplog.at_level(logging.WARN):
        await weather._update()

    assert weather._weather.is_good == False
    assert caplog.messages[0] == "Request failed: Good parameter not found in response from weather station."


@pytest.mark.asyncio
async def test_update_good_weather(caplog) -> None:
    weather = Weather("")
    weather.comm.send_event = AsyncMock()
    weather._active = True

    weather._api.get_current_status = AsyncMock(return_value={"good": True})

    with caplog.at_level(logging.INFO):
        await weather._update()

    assert caplog.messages[0] == "Weather is now good."
    assert isinstance(weather.comm.send_event.await_args[0][0], GoodWeatherEvent)


@pytest.mark.asyncio
async def test_update_bad_weather(caplog) -> None:
    weather = Weather("")
    weather._weather.is_good = True
    weather.comm.send_event = AsyncMock()
    weather._active = True

    weather._api.get_current_status = AsyncMock(return_value={"good": False})

    with caplog.at_level(logging.INFO):
        await weather._update()

    assert caplog.messages[0] == "Weather is now bad."
    assert isinstance(weather.comm.send_event.await_args[0][0], BadWeatherEvent)


def test_calc_system_init_eta() -> None:
    weather = Weather("", 600)
    pyobs.utils.time.Time.now = Mock(return_value=Time("2010-01-01T00:00:00", format='isot', scale='utc'))

    time = weather._calc_system_init_eta()
    assert time == "2010-01-01T00:10:00"


@pytest.mark.asyncio
async def test_is_weather_good() -> None:
    weather = Weather("")
    weather._active = False
    assert await weather.is_weather_good() == True

    weather._active = True

    assert await weather.is_weather_good() == False


@pytest.mark.asyncio
async def test_get_current_weather() -> None:
    weather = Weather("")
    status = {"good": True}
    weather._weather.status = status
    assert await weather.get_current_weather() == status
