from unittest.mock import AsyncMock

import pytest

from pyobs.events import BadWeatherEvent, GoodWeatherEvent
from pyobs.interfaces import IRunning, IWeather, WeatherSensorReading
from pyobs.modules import Module
from pyobs.modules.weather import MockWeather
from pyobs.utils.enums import Unit, WeatherSensors


@pytest.mark.asyncio
async def test_open() -> None:
    weather = MockWeather()
    weather._comm.register_event = AsyncMock()
    weather._comm.set_state = AsyncMock()

    Module.open = AsyncMock()

    await weather.open()

    weather._comm.register_event.assert_called()
    assert weather._comm.register_event.await_args_list[0][0][0] == BadWeatherEvent
    assert weather._comm.register_event.await_args_list[1][0][0] == GoodWeatherEvent

    assert weather._comm.set_state.await_count == 2
    interface, state = weather._comm.set_state.await_args_list[0][0]
    assert interface is IWeather
    assert state.good is True

    interface, state = weather._comm.set_state.await_args_list[1][0]
    assert interface is IRunning
    assert state.running is True


@pytest.mark.asyncio
async def test_start() -> None:
    weather = MockWeather()
    weather._comm.send_event = AsyncMock()
    weather._comm.set_state = AsyncMock()

    weather._active = False
    weather._good = False

    await weather.start()

    assert await weather.is_running() is True
    assert isinstance(weather._comm.send_event.await_args[0][0], BadWeatherEvent)


@pytest.mark.asyncio
async def test_stop() -> None:
    weather = MockWeather()
    weather._comm.set_state = AsyncMock()

    await weather.stop()

    assert await weather.is_running() is False


@pytest.mark.asyncio
async def test_is_running() -> None:
    weather = MockWeather()
    assert await weather.is_running() is True

    weather._active = False
    assert await weather.is_running() is False


@pytest.mark.asyncio
async def test_set_good_no_change() -> None:
    weather = MockWeather(good=True)
    weather._comm.send_event = AsyncMock()
    weather._comm.set_state = AsyncMock()

    await weather.set_good(True)

    assert weather._good is True
    weather._comm.send_event.assert_not_called()
    weather._comm.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_set_good_becomes_bad() -> None:
    weather = MockWeather(good=True)
    weather._comm.send_event = AsyncMock()
    weather._comm.set_state = AsyncMock()

    await weather.set_good(False)

    assert weather._good is False
    assert isinstance(weather._comm.send_event.await_args[0][0], BadWeatherEvent)

    _, state = weather._comm.set_state.await_args_list[0][0]
    assert state.good is False


@pytest.mark.asyncio
async def test_set_good_becomes_good() -> None:
    weather = MockWeather(good=False)
    weather._comm.send_event = AsyncMock()
    weather._comm.set_state = AsyncMock()

    await weather.set_good(True)

    assert weather._good is True
    assert isinstance(weather._comm.send_event.await_args[0][0], GoodWeatherEvent)


@pytest.mark.asyncio
async def test_set_good_inactive_no_event() -> None:
    weather = MockWeather(good=True)
    weather._active = False
    weather._comm.send_event = AsyncMock()
    weather._comm.set_state = AsyncMock()

    await weather.set_good(False)

    weather._comm.send_event.assert_not_called()
    _, state = weather._comm.set_state.await_args_list[0][0]
    assert state.good is True


@pytest.mark.asyncio
async def test_set_sensor_value() -> None:
    weather = MockWeather()
    weather.set_sensor_value(WeatherSensors.TEMPERATURE, 42.0)
    reading = await weather.get_sensor_value("test", WeatherSensors.TEMPERATURE)
    assert reading.value == 42.0


@pytest.mark.asyncio
async def test_get_sensor_value() -> None:
    weather = MockWeather()
    reading = await weather.get_sensor_value("test", WeatherSensors.TEMPERATURE)

    assert reading == WeatherSensorReading(
        sensor=WeatherSensors.TEMPERATURE, value=15.0, unit=Unit.CELSIUS.value, time=reading.time
    )


@pytest.mark.asyncio
async def test_get_sensor_value_invalid() -> None:
    weather = MockWeather()

    with pytest.raises(ValueError):
        await weather.get_sensor_value("test", WeatherSensors.TIME)


@pytest.mark.asyncio
async def test_init_with_custom_sensors() -> None:
    weather = MockWeather(sensors={"temp": 30.0})
    reading = await weather.get_sensor_value("test", WeatherSensors.TEMPERATURE)
    assert reading.value == 30.0


@pytest.mark.asyncio
async def test_get_fits_header_before() -> None:
    weather = MockWeather()
    weather.set_sensor_value(WeatherSensors.RAIN, 1)

    header = await weather.get_fits_header_before()

    assert header["WS-PREC"].value is True
    assert header["WS-PREC"].comment == "Ambient precipitation [0/1]"
