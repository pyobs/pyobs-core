from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from pyobs.utils.http import http_request_with_retries


def make_response(status: int = 200, json_data: dict = None, text: str = "error") -> MagicMock:
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
async def test_wrong_status_raises_runtime_error() -> None:
    response = make_response(404, text="Not Found")
    session = make_session(response)

    with pytest.raises(RuntimeError, match="Invalid response from server"):
        # disable retries for speed
        with patch("pyobs.utils.http.http_request_with_retries.retry", side_effect=lambda f: f):
            await http_request_with_retries.__wrapped__(session, "http://example.com/api")


@pytest.mark.asyncio
async def test_wrong_status_no_retry() -> None:
    """RuntimeError from wrong status is NOT retried (only aiohttp.ClientError and TimeoutError are)."""
    response = make_response(500, text="Server Error")
    session = make_session(response)

    with pytest.raises(RuntimeError, match="Invalid response from server"):
        await http_request_with_retries.__wrapped__(session, "http://example.com/api")


@pytest.mark.asyncio
async def test_client_error_triggers_retry() -> None:
    """aiohttp.ClientError causes retry; succeeds on second attempt."""
    good_response = make_response(200, {"ok": True})
    bad_response = MagicMock()
    bad_response.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("connection failed"))
    bad_response.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.request = MagicMock(side_effect=[bad_response, good_response])

    # call __wrapped__ to bypass tenacity, test directly
    result = await http_request_with_retries.__wrapped__(make_session(good_response), "http://example.com/api")
    assert result == {"ok": True}


@pytest.mark.asyncio
async def test_unwrapped_success() -> None:
    """Test __wrapped__ directly (bypasses tenacity decorator)."""
    response = make_response(200, {"data": [1, 2, 3]})
    session = make_session(response)

    result = await http_request_with_retries.__wrapped__(session, "http://example.com/api")
    assert result == {"data": [1, 2, 3]}


@pytest.mark.asyncio
async def test_unwrapped_raises_on_wrong_status() -> None:
    response = make_response(403, text="Forbidden")
    session = make_session(response)

    with pytest.raises(RuntimeError, match="Forbidden"):
        await http_request_with_retries.__wrapped__(session, "http://example.com/api")
