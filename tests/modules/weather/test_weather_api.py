from typing import Dict, Any

import pytest

from pyobs.modules.weather.weather_api import WeatherApi
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
async def test_send_valid(mocker) -> None:
    api = WeatherApi("example.com/")

    json = {"good": True}
    mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse(json, 200))

    assert await api._send("test/") == json


@pytest.mark.asyncio
async def test_send_invalid(mocker) -> None:
    api = WeatherApi("example.com/")
    mocker.patch("aiohttp.ClientSession.get", return_value=MockResponse({}, 404))

    with pytest.raises(ValueError):
        await api._send("")


@pytest.mark.asyncio
async def test_get_current_status(mocker) -> None:
    api = WeatherApi("")
    mocker.patch.object(api, "_send")
    await api.get_current_status()
    api._send.assert_called_once_with("api/current/")


@pytest.mark.asyncio
async def test_get_sensor_value(mocker) -> None:
    api = WeatherApi("")
    mocker.patch.object(api, "_send")
    await api.get_sensor_value("test", WeatherSensors.RAIN)
    api._send.assert_called_once_with("api/stations/test/rain/")
