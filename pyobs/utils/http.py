import asyncio
from typing import Any
import logging
import aiohttp
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, before_sleep_log

log = logging.getLogger(__name__)


@retry(
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(log, logging.WARNING),  # type: ignore[arg-type]
    reraise=True,
)
async def http_request_with_retries(
    session: aiohttp.ClientSession, url: str, method: str = "get", expected_status: int = 200, **kwargs: Any
) -> dict[str, Any] | list[Any]:
    async with session.request(method, url, **kwargs) as response:
        if response.status != expected_status:
            raise RuntimeError("Invalid response from server: " + await response.text())
        return await response.json()
