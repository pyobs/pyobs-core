import urllib.parse
from typing import Any, cast
import aiohttp

from pyobs.utils.enums import WeatherSensors


class WeatherApi(object):
    TIMEOUT = 5

    def __init__(self, url: str) -> None:
        self._url = url

    async def get_current_status(self) -> dict[str, Any]:
        return await self._send("api/current/")

    async def get_sensor_value(self, station: str, sensor: WeatherSensors) -> dict[str, Any]:
        path = f"api/stations/{station}/{sensor.value}/"
        return await self._send(path)

    async def _send(self, path: str) -> dict[str, Any]:
        url = urllib.parse.urljoin(self._url, path)
        async with aiohttp.ClientSession() as session:
            return await self._get_response(url, session)

    async def _get_response(self, url: str, session: aiohttp.ClientSession, max_attempts: int = 3) -> dict[str, Any]:
        attempt = 0
        while attempt < max_attempts:
            async with session.get(url, timeout=self.TIMEOUT) as response:
                if response.status == 200:
                    return cast(dict[str, Any], await response.json())
            attempt += 1
        raise ValueError("Could not connect to weather station.")
