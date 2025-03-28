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
            return await self._get_response(url, session)

    async def _get_response(self, url, session):
        async with session.get(url, timeout=self.TIMEOUT) as response:
            if await self._check_valid_response(response):
                return await response.json()

    @staticmethod
    async def _check_valid_response(response, max_attempts: int=3) -> bool:
        attempt = 0
        while attempt < max_attempts:
            if response.status == 200:
                return True
            attempt += 1
        raise ValueError("Could not connect to weather station.")