import asyncio
import logging
import time
from typing import Any, cast

import aiohttp
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

log = logging.getLogger(__name__)

# Per-URL (first-failure time, last-warned time) for throttling retry warnings, see
# _before_sleep. A URL is only present here while it is currently failing; a successful
# request clears its entry.
_failure_state: dict[str, tuple[float, float | None]] = {}

# Retries stay quiet for this long after the first failure (an in-progress deploy of the
# remote service typically resolves within this window), then warn at most this often.
_WARN_AFTER_SECONDS = 60.0
_WARN_INTERVAL_SECONDS = 60.0


class InvalidResponseError(RuntimeError):
    """Raised when the server returns an unexpected HTTP status. Carries the status and, if
    available, the parsed JSON body, so callers can distinguish specific failure modes."""

    def __init__(self, status: int, body: Any = None):
        self.status = status
        self.body = body
        super().__init__(f"Invalid response from server: HTTP {status}")


def _before_sleep(retry_state: RetryCallState) -> None:
    url = cast(str, retry_state.kwargs.get("url", retry_state.args[1] if len(retry_state.args) > 1 else None))
    now = time.monotonic()
    first_failure, last_warned = _failure_state.setdefault(url, (now, None))

    exc = retry_state.outcome.exception() if retry_state.outcome else None
    elapsed = now - first_failure
    if elapsed >= _WARN_AFTER_SECONDS and (last_warned is None or now - last_warned >= _WARN_INTERVAL_SECONDS):
        log.warning("Still failing to reach %s after %.0fs: %s: %s", url, elapsed, type(exc).__name__, exc)
        _failure_state[url] = (first_failure, now)
    else:
        log.debug("Retrying %s: %s: %s", url, type(exc).__name__, exc)


@retry(
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError, RuntimeError)),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_attempt(5),
    before_sleep=_before_sleep,
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
        _failure_state.pop(url, None)
        return cast(dict[str, Any], await response.json())


async def http_request_paginated(
    session: aiohttp.ClientSession,
    url: str,
    method: str = "get",
    expected_status: int = 200,
    strict: bool = False,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Fetches all pages of a DRF-style paginated list endpoint and returns the combined results.

    If a page beyond the first becomes invalid mid-fetch (DRF's "Invalid page." 404, which can
    happen when concurrent writes shift page boundaries on a live-growing dataset), pagination
    stops early with whatever was already fetched instead of failing the whole request. With
    ``strict=True`` that truncation is raised as an error instead, so callers that treat the
    result as authoritative (e.g. replacing a cached list) never apply a partial result silently.
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
                if strict:
                    log.warning(
                        "Pagination page became invalid mid-fetch, raising instead of returning a "
                        "truncated result of %d item(s).",
                        len(results),
                    )
                    raise
                log.warning("Pagination page became invalid mid-fetch, stopping early with %d result(s).", len(results))
                break
            raise
        results.extend(data["results"])
        next_url = data.get("next")
        kwargs = {}
        is_first_page = False
    return results
