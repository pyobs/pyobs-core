import urllib.parse
from typing import Any, Dict

import aiohttp
from pyobs.utils.enums import WeatherSensors


class WeatherApi(object):
    TIMEOUT = 5

    def __init__(self, url: str) -> None:
        self._url = url

    async def get_current_status(self) -> Dict[str, Any]:
        return await self._send("api/current/")

    async def get_sensor_value(self, station: str, sensor: WeatherSensors) -> Dict[str, Any]:
        path = f"api/stations/{station}/{sensor.value}/"
        return await self._send(path)

    async def _send(self, path: str) -> Dict[str, Any]:
        url = urllib.parse.urljoin(self._url, path)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=self.TIMEOUT) as response:
                if response.status != 200:
                    raise ValueError("Could not connect to weather station.")
                return await response.json()
