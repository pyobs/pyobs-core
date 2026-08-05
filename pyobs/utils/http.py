import asyncio
import logging
from typing import Any, cast

import aiohttp
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

log = logging.getLogger(__name__)


@retry(
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError, RuntimeError)),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
async def http_request_with_retries(
    session: aiohttp.ClientSession, url: str, method: str = "get", expected_status: int = 200, **kwargs: Any
) -> dict[str, Any]:
    async with session.request(method, url, **kwargs) as response:
        if response.status != expected_status:
            raise RuntimeError(f"Invalid response from server: HTTP {response.status}")
        return cast(dict[str, Any], await response.json())


async def http_request_paginated(
    session: aiohttp.ClientSession, url: str, method: str = "get", expected_status: int = 200, **kwargs: Any
) -> list[dict[str, Any]]:
    """Fetches all pages of a DRF-style paginated list endpoint and returns the combined results."""
    results: list[dict[str, Any]] = []
    next_url: str | None = url
    while next_url is not None:
        data = await http_request_with_retries(
            session, next_url, method=method, expected_status=expected_status, **kwargs
        )
        results.extend(data["results"])
        next_url = data.get("next")
        kwargs = {}
    return results
