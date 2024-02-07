import asyncio
import logging
from typing import Dict, Any
from unittest.mock import AsyncMock

import aiohttp
import pytest

from pyobs.comm.dummy import DummyComm
from pyobs.events import GoodWeatherEvent, BadWeatherEvent
from pyobs.modules import Module
from pyobs.modules.weather import Weather
from pyobs.utils.enums import WeatherSensors


class MockResponse:
    def __init__(self, json: Dict[str, Any], status=200) -> None:
        self._json = json
        self.status = status

    async def json(self) -> Dict[str, Any]:
        return self._json

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self

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
async def test_get_sensor_value(mocker):
    weather = Weather("example.com/")

    mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse({}, 404))

    with pytest.raises(ValueError):
        await weather.get_sensor_value("test", WeatherSensors.RAIN)

    aiohttp.ClientSession.get.assert_called_once_with("example.com/api/stations/test/rain/", timeout=5)


@pytest.mark.asyncio
async def test_get_fits_header_before_invalid(caplog) -> None:
    weather = Weather("")

    with caplog.at_level(logging.ERROR):
        assert await weather.get_fits_header_before() == {}


@pytest.mark.asyncio
async def test_get_fits_header_before(caplog) -> None:
    weather = Weather("")
    weather._status["sensors"] = {"rain": {"value": 1}}

    header = await weather.get_fits_header_before()
    assert header["WS-PREC"] == (True, "Ambient precipitation [0/1]")


@pytest.mark.asyncio
async def test_update_invalid_response(mocker, caplog) -> None:
    weather = Weather("example.com/")

    mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse({}, 404))
    mocker.patch("asyncio.sleep")

    with caplog.at_level(logging.WARN):
        await weather._update()

    assert weather._is_good == False
    assert caplog.messages[0] == "Request failed: Could not connect to weather station."

    aiohttp.ClientSession.get.assert_called_once_with("example.com/api/current/", timeout=5)
    asyncio.sleep.assert_called_once_with(60)


@pytest.mark.asyncio
async def test_update_invalid_response(mocker, caplog) -> None:
    weather = Weather("example.com/")

    mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse({}, 200))
    mocker.patch("asyncio.sleep")

    with caplog.at_level(logging.WARN):
        await weather._update()

    assert weather._is_good == False
    assert caplog.messages[0] == "Request failed: Good parameter not found in response from weather station."

@pytest.mark.asyncio
async def test_update_good_weather(mocker, caplog) -> None:
    weather = Weather("")
    weather.comm.send_event = AsyncMock()
    weather._active = True

    mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse({"good": True}, 200))
    mocker.patch("asyncio.sleep")

    with caplog.at_level(logging.INFO):
        await weather._update()

    assert caplog.messages[0] == "Weather is now good."
    assert isinstance(weather.comm.send_event.await_args[0][0], GoodWeatherEvent)

    asyncio.sleep.assert_called_once_with(5)


@pytest.mark.asyncio
async def test_update_bad_weather(mocker, caplog) -> None:
    weather = Weather("")
    weather._is_good = True
    weather.comm.send_event = AsyncMock()
    weather._active = True

    mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse({"good": False}, 200))
    mocker.patch("asyncio.sleep")

    with caplog.at_level(logging.INFO):
        await weather._update()

    assert caplog.messages[0] == "Weather is now bad."
    assert isinstance(weather.comm.send_event.await_args[0][0], BadWeatherEvent)