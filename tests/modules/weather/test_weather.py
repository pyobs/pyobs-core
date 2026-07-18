import asyncio
import logging
from unittest.mock import AsyncMock, Mock

import pytest

import pyobs
from pyobs.events import BadWeatherEvent, GoodWeatherEvent
from pyobs.interfaces import IWeather, WeatherSensorReading
from pyobs.modules import Module
from pyobs.modules.weather import Weather
from pyobs.modules.weather.weather import WeatherResponseError
from pyobs.utils.enums import Unit, WeatherSensors
from pyobs.utils.time import Time


@pytest.mark.asyncio
async def test_open() -> None:
    weather = Weather("")
    weather._comm.register_event = AsyncMock()

    Module.open = AsyncMock()

    await weather.open()

    weather._comm.register_event.assert_called()

    assert weather._comm.register_event.await_args_list[0][0][0] == BadWeatherEvent
    assert weather._comm.register_event.await_args_list[1][0][0] == GoodWeatherEvent


@pytest.mark.asyncio
async def test_start() -> None:
    weather = Weather("")
    weather._comm.send_event = AsyncMock()

    weather._active = False

    await weather.start()

    assert await weather.is_running() is True
    assert isinstance(weather._comm.send_event.await_args[0][0], BadWeatherEvent)


@pytest.mark.asyncio
async def test_stop() -> None:
    weather = Weather("")
    await weather.stop()
    assert await weather.is_running() is False


@pytest.mark.asyncio
async def test_is_running() -> None:
    weather = Weather("")
    assert await weather.is_running() is True

    await weather.stop()
    assert await weather.is_running() is False


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
    with pytest.raises(WeatherResponseError):
        await weather.get_sensor_value("test", WeatherSensors.RAIN)


@pytest.mark.asyncio
async def test_get_sensor_value():
    weather = Weather("example.com/")

    weather._api.get_sensor_value = AsyncMock(return_value={"time": "2026-07-02T08:36:42", "value": 2})
    reading = await weather.get_sensor_value("test", WeatherSensors.RAIN)

    assert reading == WeatherSensorReading(
        sensor=WeatherSensors.RAIN,
        value=2,
        unit="bool",
        time=Time("2026-07-02T08:36:42", format="isot", scale="utc"),
    )


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
    assert header["WS-PREC"].value is True
    assert header["WS-PREC"].comment == "Ambient precipitation [0/1]"


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

    assert weather._weather.is_good is False
    assert caplog.messages[0] == "Request failed: Could not connect to weather station."

    weather._api.get_current_status.assert_called_once_with()


@pytest.mark.asyncio
async def test_update_invalid_response(caplog) -> None:
    weather = Weather("example.com/")

    weather._api.get_current_status = AsyncMock(return_value={})

    with caplog.at_level(logging.WARN):
        await weather._update()

    assert weather._weather.is_good is False
    assert caplog.messages[0] == "Request failed: Good parameter not found in response from weather station."


@pytest.mark.asyncio
async def test_update_good_weather(caplog) -> None:
    weather = Weather("")
    weather._comm.send_event = AsyncMock()

    weather._api.get_current_status = AsyncMock(return_value={"good": True})

    with caplog.at_level(logging.INFO):
        await weather._update()

    assert caplog.messages[0] == "Weather is now good."
    assert isinstance(weather._comm.send_event.await_args[0][0], GoodWeatherEvent)


@pytest.mark.asyncio
async def test_update_bad_weather(caplog) -> None:
    weather = Weather("")
    weather._weather.is_good = True
    weather._comm.send_event = AsyncMock()

    weather._api.get_current_status = AsyncMock(return_value={"good": False})

    with caplog.at_level(logging.INFO):
        await weather._update()

    assert caplog.messages[0] == "Weather is now bad."
    assert isinstance(weather._comm.send_event.await_args[0][0], BadWeatherEvent)


def test_calc_system_init_eta() -> None:
    weather = Weather("", 600)
    pyobs.utils.time.Time.now = Mock(return_value=Time("2010-01-01T00:00:00", format="isot", scale="utc"))

    time = weather._calc_system_init_eta()
    assert time == "2010-01-01T00:10:00"


@pytest.mark.asyncio
async def test_update_publishes_state() -> None:
    weather = Weather("")
    weather._comm.set_state = AsyncMock()

    weather._api.get_current_status = AsyncMock(
        return_value={"good": True, "sensors": {"temp": {"value": 12.3}, "rain": {"value": None}}}
    )

    await weather._update()

    weather._comm.set_state.assert_awaited_once()
    interface, state = weather._comm.set_state.await_args[0]
    assert interface is IWeather
    assert state.good is True
    assert len(state.readings) == 1
    assert (state.readings[0].sensor, state.readings[0].value, state.readings[0].unit) == (
        WeatherSensors.TEMPERATURE,
        12.3,
        Unit.CELSIUS.value,
    )


@pytest.mark.asyncio
async def test_update_publishes_good_when_inactive() -> None:
    weather = Weather("")
    weather._comm.set_state = AsyncMock()
    weather._active = False

    weather._api.get_current_status = AsyncMock(return_value={"good": False})

    await weather._update()

    _, state = weather._comm.set_state.await_args[0]
    assert state.good is True


def test_get_readings() -> None:
    weather = Weather("")
    weather._weather.status = {
        "good": True,
        "sensors": {
            "temp": {"value": 12.3},
            "humid": {"value": None},
            "windspeed": {"value": 5.0},
        },
    }

    readings = weather._get_readings()
    assert [(r.sensor, r.value, r.unit) for r in readings] == [
        (WeatherSensors.TEMPERATURE, 12.3, Unit.CELSIUS.value),
        (WeatherSensors.WINDSPEED, 5.0, Unit.KM_PER_HOUR.value),
    ]


def test_get_readings_no_sensors() -> None:
    weather = Weather("")
    assert weather._get_readings() == []
