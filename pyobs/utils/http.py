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


class InvalidResponseError(RuntimeError):
    """Raised when the server returns an unexpected HTTP status. Carries the status and, if
    available, the parsed JSON body, so callers can distinguish specific failure modes."""

    def __init__(self, status: int, body: Any = None):
        self.status = status
        self.body = body
        super().__init__(f"Invalid response from server: HTTP {status}")


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
            body = None
            try:
                body = await response.json()
            except (aiohttp.ContentTypeError, ValueError):
                pass
            raise InvalidResponseError(response.status, body)
        return cast(dict[str, Any], await response.json())


async def http_request_paginated(
    session: aiohttp.ClientSession, url: str, method: str = "get", expected_status: int = 200, **kwargs: Any
) -> list[dict[str, Any]]:
    """Fetches all pages of a DRF-style paginated list endpoint and returns the combined results.

    If a page beyond the first becomes invalid mid-fetch (DRF's "Invalid page." 404, which can
    happen when concurrent writes shift page boundaries on a live-growing dataset), pagination
    stops early with whatever was already fetched instead of failing the whole request.
    """
    results: list[dict[str, Any]] = []
    next_url: str | None = url
    is_first_page = True
    while next_url is not None:
        try:
            data = await http_request_with_retries(
                session, next_url, method=method, expected_status=expected_status, **kwargs
            )
        except InvalidResponseError as e:
            if (
                not is_first_page
                and e.status == 404
                and isinstance(e.body, dict)
                and e.body.get("detail") == "Invalid page."
            ):
                log.warning("Pagination page became invalid mid-fetch, stopping early with %d result(s).", len(results))
                break
            raise
        results.extend(data["results"])
        next_url = data.get("next")
        kwargs = {}
        is_first_page = False
    return results
