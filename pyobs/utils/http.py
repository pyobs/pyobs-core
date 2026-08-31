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


class LogThrottle:
    """Escalates a repeated failure from quiet to a louder log level, without spamming on every
    occurrence.

    Tracks, per key, when a failure streak started and when it was last escalated. A key stays
    quiet for ``quiet_for`` seconds after its first failure, then :meth:`should_escalate` returns
    ``True`` at most once every ``interval`` seconds. :meth:`clear` must be called on success, or
    a key's state (and thus memory) is retained forever -- callers are responsible for using a
    bounded/stable set of keys (e.g. a fixed URL, not one that varies per call), since each
    distinct key gets its own independent streak and never expires on its own.
    """

    def __init__(self, quiet_for: float = 60.0, interval: float = 60.0) -> None:
        self._quiet_for = quiet_for
        self._interval = interval
        self._state: dict[str, tuple[float, float | None]] = {}

    def should_escalate(self, key: str) -> bool:
        now = time.monotonic()
        first_failure, last_escalated = self._state.setdefault(key, (now, None))
        if now - first_failure >= self._quiet_for and (
            last_escalated is None or now - last_escalated >= self._interval
        ):
            self._state[key] = (first_failure, now)
            return True
        return False

    def clear(self, key: str) -> None:
        self._state.pop(key, None)


# Retries stay quiet for this long after the first failure to a given URL (an in-progress deploy
# of the remote service typically resolves within this window), then warn at most this often.
_retry_throttle = LogThrottle(quiet_for=60.0, interval=60.0)


class InvalidResponseError(RuntimeError):
    """Raised when the server returns an unexpected HTTP status. Carries the status and, if
    available, the parsed JSON body, so callers can distinguish specific failure modes."""

    def __init__(self, status: int, body: Any = None):
        self.status = status
        self.body = body
        super().__init__(f"Invalid response from server: HTTP {status}")


def _before_sleep(retry_state: RetryCallState) -> None:
    url = retry_state.kwargs.get("url") or (retry_state.args[1] if len(retry_state.args) > 1 else None)
    assert isinstance(url, str), "http_request_with_retries must be called with a url"

    exc = retry_state.outcome.exception() if retry_state.outcome else None
    if _retry_throttle.should_escalate(url):
        log.warning("Still failing to reach %s: %s: %s", url, type(exc).__name__, exc)
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
        _retry_throttle.clear(url)
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
