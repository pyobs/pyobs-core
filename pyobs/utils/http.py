import asyncio
from typing import Any

import aiohttp
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type


@retry(
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_attempt(5),
    reraise=True,
)
async def http_request_with_retries(
    session: aiohttp.ClientSession, url: str, method: str = "get", expected_status: int = 200, **kwargs: Any
) -> dict[str, Any] | list[Any]:
    async with session.request(method, url, **kwargs) as response:
        if response.status != expected_status:
            raise RuntimeError("Invalid response from server: " + await response.text())
        return await response.json()
