from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock

import aiohttp
import pytest

import pyobs.utils.http as httpmod
from pyobs.utils.http import http_request_paginated, http_request_with_retries


def make_response(status: int = 200, json_data: dict | None = None, text: str = "error") -> MagicMock:
    """Create a mock aiohttp response."""
    response = MagicMock()
    response.status = status
    response.json = AsyncMock(return_value=json_data or {})
    response.text = AsyncMock(return_value=text)
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=False)
    return response


def make_session(response: MagicMock) -> MagicMock:
    session = MagicMock()
    session.request = MagicMock(return_value=response)
    return session


# ── happy path ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_request_returns_json() -> None:
    response = make_response(200, {"key": "value"})
    session = make_session(response)

    result = await http_request_with_retries(session, "http://example.com/api")

    assert result == {"key": "value"}
    session.request.assert_called_once_with("get", "http://example.com/api")


@pytest.mark.asyncio
async def test_post_request() -> None:
    response = make_response(200, {"created": True})
    session = make_session(response)

    result = await http_request_with_retries(session, "http://example.com/api", method="post", json={"name": "test"})

    assert result == {"created": True}
    session.request.assert_called_once_with("post", "http://example.com/api", json={"name": "test"})


@pytest.mark.asyncio
async def test_custom_expected_status() -> None:
    response = make_response(201, {"id": 42})
    session = make_session(response)

    result = await http_request_with_retries(session, "http://example.com/api", method="post", expected_status=201)

    assert result == {"id": 42}


@pytest.mark.asyncio
async def test_passes_extra_kwargs_to_request() -> None:
    response = make_response(200, {})
    session = make_session(response)

    await http_request_with_retries(session, "http://example.com/api", params={"q": "test"}, headers={"X-Token": "abc"})

    session.request.assert_called_once_with(
        "get", "http://example.com/api", params={"q": "test"}, headers={"X-Token": "abc"}
    )


# ── error handling ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_wrong_status_is_retried() -> None:
    """RuntimeError from a wrong status code (e.g. 502 Bad Gateway) is retried."""
    response = make_response(502, text="Bad Gateway")
    session = make_session(response)

    with pytest.raises(RuntimeError, match="HTTP 502"):
        await http_request_with_retries.__wrapped__(session, "http://example.com/api")


@pytest.mark.asyncio
async def test_client_error_raises_on_wrapped() -> None:
    """aiohttp.ClientError propagates out of __wrapped__ (retries are handled by tenacity wrapper)."""
    bad_response = MagicMock()
    bad_response.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("connection failed"))
    bad_response.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.request = MagicMock(return_value=bad_response)

    with pytest.raises(aiohttp.ClientError):
        await http_request_with_retries.__wrapped__(session, "http://example.com/api")


@pytest.mark.asyncio
async def test_unwrapped_success() -> None:
    """Test __wrapped__ directly (bypasses tenacity decorator)."""
    response = make_response(200, {"data": [1, 2, 3]})
    session = make_session(response)

    result = await http_request_with_retries.__wrapped__(session, "http://example.com/api")
    assert result == {"data": [1, 2, 3]}


@pytest.mark.asyncio
async def test_unwrapped_raises_on_wrong_status() -> None:
    """Error message contains the HTTP status code, not the response body."""
    response = make_response(403, text="Forbidden")
    session = make_session(response)

    with pytest.raises(RuntimeError, match="HTTP 403"):
        await http_request_with_retries.__wrapped__(session, "http://example.com/api")


# ── http_request_paginated ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_paginated_single_page() -> None:
    response = make_response(200, {"results": [{"id": 1}, {"id": 2}], "next": None})
    session = make_session(response)

    result = await http_request_paginated(session, "http://example.com/api")

    assert result == [{"id": 1}, {"id": 2}]
    session.request.assert_called_once_with("get", "http://example.com/api")


@pytest.mark.asyncio
async def test_paginated_follows_next_until_exhausted() -> None:
    page1 = make_response(200, {"results": [{"id": 1}], "next": "http://example.com/api?page=2"})
    page2 = make_response(200, {"results": [{"id": 2}], "next": None})
    session = MagicMock()
    session.request = MagicMock(side_effect=[page1, page2])

    result = await http_request_paginated(session, "http://example.com/api")

    assert result == [{"id": 1}, {"id": 2}]
    assert session.request.call_count == 2
    session.request.assert_any_call("get", "http://example.com/api")
    session.request.assert_any_call("get", "http://example.com/api?page=2")


@pytest.mark.asyncio
async def test_paginated_only_passes_kwargs_to_first_request() -> None:
    """params etc. are baked into the "next" URL by the server -- passing them again on
    follow-up requests would duplicate query params."""
    page1 = make_response(200, {"results": [{"id": 1}], "next": "http://example.com/api?page=2"})
    page2 = make_response(200, {"results": [{"id": 2}], "next": None})
    session = MagicMock()
    session.request = MagicMock(side_effect=[page1, page2])

    await http_request_paginated(session, "http://example.com/api", params={"state": "pending"})

    session.request.assert_any_call("get", "http://example.com/api", params={"state": "pending"})
    session.request.assert_any_call("get", "http://example.com/api?page=2")


@pytest.mark.asyncio
async def test_paginated_stops_early_on_invalid_page_beyond_first(monkeypatch: pytest.MonkeyPatch) -> None:
    """A page shifting out of range mid-fetch (e.g. concurrent writes on a live dataset) stops
    pagination with the results gathered so far, instead of failing the whole request."""
    monkeypatch.setattr(httpmod, "http_request_with_retries", http_request_with_retries.__wrapped__)
    page1 = make_response(200, {"results": [{"id": 1}], "next": "http://example.com/api?page=2"})
    page2 = make_response(404, {"detail": "Invalid page."})
    session = MagicMock()
    session.request = MagicMock(side_effect=[page1, page2])

    result = await http_request_paginated(session, "http://example.com/api")

    assert result == [{"id": 1}]


@pytest.mark.asyncio
async def test_paginated_strict_raises_on_invalid_page_beyond_first(monkeypatch: pytest.MonkeyPatch) -> None:
    """With strict=True a truncated result is an error, so callers that replace a cached list with
    the fetched content never apply a partial result as if it were authoritative."""
    monkeypatch.setattr(httpmod, "http_request_with_retries", http_request_with_retries.__wrapped__)
    page1 = make_response(200, {"results": [{"id": 1}], "next": "http://example.com/api?page=2"})
    page2 = make_response(404, {"detail": "Invalid page."})
    session = MagicMock()
    session.request = MagicMock(side_effect=[page1, page2])

    with pytest.raises(RuntimeError, match="HTTP 404"):
        await http_request_paginated(session, "http://example.com/api", strict=True)


@pytest.mark.asyncio
async def test_paginated_does_not_swallow_invalid_page_on_first_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """An "Invalid page." 404 on the very first request is a real error (e.g. a bad page= param
    passed in by the caller), not a mid-fetch race -- it must still raise."""
    monkeypatch.setattr(httpmod, "http_request_with_retries", http_request_with_retries.__wrapped__)
    response = make_response(404, {"detail": "Invalid page."})
    session = make_session(response)

    with pytest.raises(RuntimeError, match="HTTP 404"):
        await http_request_paginated(session, "http://example.com/api")


# ── LogThrottle ──────────────────────────────────────────────────────────────


def test_log_throttle_quiet_before_threshold() -> None:
    throttle = httpmod.LogThrottle(quiet_for=60.0, interval=60.0)
    assert not throttle.should_escalate("key")


def test_log_throttle_escalates_once_past_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    throttle = httpmod.LogThrottle(quiet_for=60.0, interval=60.0)
    t = [1000.0]
    monkeypatch.setattr(httpmod.time, "monotonic", lambda: t[0])

    assert not throttle.should_escalate("key")  # t=1000, first failure
    t[0] += 60.0  # t=1060, past the threshold
    assert throttle.should_escalate("key")


def test_log_throttle_throttles_repeated_escalation(monkeypatch: pytest.MonkeyPatch) -> None:
    throttle = httpmod.LogThrottle(quiet_for=60.0, interval=60.0)
    t = [1000.0]
    monkeypatch.setattr(httpmod.time, "monotonic", lambda: t[0])

    throttle.should_escalate("key")  # t=1000, first failure
    t[0] += 60.0  # t=1060, escalates
    assert throttle.should_escalate("key")
    t[0] += 1  # t=1061, still within the throttle window
    assert not throttle.should_escalate("key")
    t[0] += 60.0  # past the throttle window again
    assert throttle.should_escalate("key")


def test_log_throttle_zero_quiet_for_escalates_immediately() -> None:
    """quiet_for=0.0 is the caller-error-loop policy: alert on the first failure, then throttle."""
    throttle = httpmod.LogThrottle(quiet_for=0.0, interval=60.0)
    assert throttle.should_escalate("key")
    assert not throttle.should_escalate("key")


def test_log_throttle_clear_resets_the_streak(monkeypatch: pytest.MonkeyPatch) -> None:
    throttle = httpmod.LogThrottle(quiet_for=60.0, interval=60.0)
    t = [1000.0]
    monkeypatch.setattr(httpmod.time, "monotonic", lambda: t[0])

    throttle.should_escalate("key")  # t=1000, first failure
    t[0] += 60.0
    assert throttle.should_escalate("key")

    throttle.clear("key")
    assert not throttle.should_escalate("key")  # fresh streak, quiet again


def test_log_throttle_keys_are_independent() -> None:
    throttle = httpmod.LogThrottle(quiet_for=0.0, interval=60.0)
    assert throttle.should_escalate("a")
    assert throttle.should_escalate("b")  # not throttled by "a"'s escalation


# ── retry-warning throttling ────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_retry_throttle() -> None:
    """_retry_throttle is module-level and keyed by URL, so tests must not leak into each other."""
    httpmod._retry_throttle._state.clear()


def make_retry_state(url: str, exception: Exception, via_kwargs: bool = False) -> Mock:
    outcome = Mock()
    outcome.exception = Mock(return_value=exception)
    state = Mock()
    state.kwargs = {"url": url} if via_kwargs else {}
    state.args = (Mock(),) if via_kwargs else (Mock(), url)
    state.outcome = outcome
    return state


def test_before_sleep_stays_quiet_before_threshold(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("DEBUG", logger="pyobs.utils.http")
    state = make_retry_state("http://example.com/api", aiohttp.ClientError("down"))

    httpmod._before_sleep(state)

    assert not any(r.levelname == "WARNING" for r in caplog.records)
    assert any(r.levelname == "DEBUG" for r in caplog.records)


def test_before_sleep_extracts_url_from_kwargs(caplog: pytest.LogCaptureFixture) -> None:
    """url can also arrive as a kwarg (retry_state.kwargs), not just positionally."""
    caplog.set_level("DEBUG", logger="pyobs.utils.http")
    state = make_retry_state("http://example.com/api", aiohttp.ClientError("down"), via_kwargs=True)

    httpmod._before_sleep(state)

    assert "http://example.com/api" in httpmod._retry_throttle._state


def test_before_sleep_warns_once_past_threshold(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("DEBUG", logger="pyobs.utils.http")
    url = "http://example.com/api"
    exc = aiohttp.ClientError("down")

    t = [1000.0]
    monkeypatch.setattr(httpmod.time, "monotonic", lambda: t[0])

    httpmod._before_sleep(make_retry_state(url, exc))  # first failure, t=1000
    t[0] += httpmod._retry_throttle._quiet_for  # t=1060, past the threshold
    httpmod._before_sleep(make_retry_state(url, exc))

    assert sum(1 for r in caplog.records if r.levelname == "WARNING") == 1


def test_before_sleep_throttles_repeated_warnings(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("DEBUG", logger="pyobs.utils.http")
    url = "http://example.com/api"
    exc = aiohttp.ClientError("down")

    t = [1000.0]
    monkeypatch.setattr(httpmod.time, "monotonic", lambda: t[0])

    httpmod._before_sleep(make_retry_state(url, exc))  # t=1000, first failure
    t[0] += httpmod._retry_throttle._quiet_for  # t=1060, warns
    httpmod._before_sleep(make_retry_state(url, exc))
    t[0] += 1  # t=1061, still within the throttle window
    httpmod._before_sleep(make_retry_state(url, exc))

    assert sum(1 for r in caplog.records if r.levelname == "WARNING") == 1

    t[0] += httpmod._retry_throttle._interval  # past the throttle window again
    httpmod._before_sleep(make_retry_state(url, exc))

    assert sum(1 for r in caplog.records if r.levelname == "WARNING") == 2


@pytest.mark.asyncio
async def test_success_clears_failure_state() -> None:
    url = "http://example.com/api"
    httpmod._retry_throttle._state[url] = (0.0, None)

    response = make_response(200, {"ok": True})
    session = make_session(response)
    await http_request_with_retries.__wrapped__(session, url)

    assert url not in httpmod._retry_throttle._state


@pytest.mark.asyncio
async def test_paginated_does_not_swallow_unrelated_404(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 404 that isn't DRF's "Invalid page." shape (e.g. a wrong URL) must still raise."""
    monkeypatch.setattr(httpmod, "http_request_with_retries", http_request_with_retries.__wrapped__)
    page1 = make_response(200, {"results": [{"id": 1}], "next": "http://example.com/api?page=2"})
    page2 = make_response(404, {"detail": "Not found."})
    session = MagicMock()
    session.request = MagicMock(side_effect=[page1, page2])

    with pytest.raises(RuntimeError, match="HTTP 404"):
        await http_request_paginated(session, "http://example.com/api")
