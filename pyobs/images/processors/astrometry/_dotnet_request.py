from __future__ import annotations

from typing import Any
import aiohttp

import pyobs.utils.exceptions as exc


class _DotNetRequest:
    def __init__(self, request_data: dict[str, Any]):
        self._request_data = request_data

        self._response_data: dict[str, Any] | None = None
        self._status_code: int | None = None

    async def _send_request(self, url: str, timeout: int) -> None:
        to = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=self._request_data, timeout=to) as response:
                self._status_code = response.status
                self._response_data = await response.json()

    def _generate_request_error_msg(self) -> str:
        if self._response_data is None or "error" not in self._response_data:
            return "Could not connect to astrometry service."

        if self._response_data["error"] == "Could not find WCS file.":
            return "Could not determine WCS."

        return f"Received error from astrometry service: {self._response_data['error']}"

    def _handle_request_error(self) -> None:
        error_msg = self._generate_request_error_msg()
        raise exc.ImageError(error_msg)

    def _has_request_error(self) -> bool:
        return (
            self._status_code is None
            or self._response_data is None
            or self._status_code != 200
            or "error" in self._response_data
        )

    async def send(self, url: str, timeout: int) -> None:
        await self._send_request(url, timeout)

        if self._has_request_error():
            self._handle_request_error()

    @property
    def request_data(self) -> dict[str, Any]:
        return self._request_data

    @property
    def response_data(self) -> dict[str, Any] | None:
        return self._response_data
