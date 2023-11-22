from typing import Dict, Optional

import aiohttp

import pyobs.utils.exceptions as exc


class _DotNetRequest:
    def __init__(self, request_data: Dict[str, any]):
        self._request_data = request_data

        self._response_data: Optional[Dict[str, any]] = None
        self._status_code: Optional[int] = None

    async def _send_request(self, url: str, timeout: int):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=self._request_data, timeout=timeout) as response:
                self._status_code = response.status
                self._response_data = await response.json()

    def _generate_request_error_msg(self) -> str:
        if "error" not in self._response_data:
            return "Could not connect to astrometry service."

        if self._response_data["error"] == "Could not find WCS file.":
            return "Could not determine WCS."

        return f"Received error from astrometry service: {self._response_data['error']}"

    def _handle_request_error(self):
        error_msg = self._generate_request_error_msg()
        raise exc.ImageError(error_msg)

    def _is_request_successful(self) -> bool:
        return self._status_code != 200 or "error" in self._response_data

    async def send(self, url: str, timeout: int):
        await self._send_request(url, timeout)

        if self._is_request_successful():
            self._handle_request_error()

    @property
    def request_data(self) -> Dict[str, any]:
        return self._request_data

    @property
    def response_data(self) -> Optional[Dict[str, any]]:
        return self._response_data
