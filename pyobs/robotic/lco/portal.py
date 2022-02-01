from typing import Any, Dict, List, cast
from urllib.parse import urljoin

import aiohttp

from pyobs.utils.time import Time


class Portal:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token

    async def _get(self, path: str, timeout: int = 10) -> Any:
        """Do a GET request on the portal.

        Args:
            url: URL to request.

        Returns:
            Response for request.

        Raises:
            RuntimeError if the call failed.
            TimeoutError if the call timed out.
        """

        # build header
        headers = {"Authorization": "Token " + self.token}

        async with aiohttp.ClientSession() as session:
            async with session.get(urljoin(self.url, path), headers=headers, timeout=timeout) as response:
                if response.status != 200:
                    raise RuntimeError("Invalid response from portal: " + await response.text())
                return await response.json()

    async def last_changed(self) -> Time:
        t = await self._get("/api/last_changed/")
        return Time(t["last_change_time"])

    async def last_scheduled(self) -> Time:
        t = await self._get("/api/last_scheduled/")
        return Time(t["last_schedule_time"])

    async def schedulable_requests(self) -> List[Dict[str, Any]]:
        req = await self._get("/api/requestgroups/schedulable_requests/")
        return cast(List[Dict[str, Any]], req)

    async def proposals(self) -> List[Dict[str, Any]]:
        req = await self._get("/api/proposals/")
        return cast(List[Dict[str, Any]], req["results"])

    async def instruments(self) -> Dict[str, Any]:
        req = await self._get("/api/instruments/")
        return cast(Dict[str, Any], req)
