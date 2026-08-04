from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from aiohttp import web

from pyobs.comm import Comm
from pyobs.modules.utils.httpfilecache import HttpFileCache


def make_cache(**kwargs: object) -> HttpFileCache:
    comm = MagicMock(spec=Comm)
    return HttpFileCache(comm=comm, **kwargs)


def make_request(headers: dict[str, str] | None = None, filename: str = "test.txt") -> MagicMock:
    request = MagicMock(spec=web.Request)
    request.headers = headers or {}
    request.match_info = {"filename": filename}
    return request


# ── auth ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_download_without_token_configured_is_unauthenticated() -> None:
    cache = make_cache()
    cache._cache["test.txt"] = b"data"
    response = await cache.download_handler(make_request())
    assert response.body == b"data"


@pytest.mark.asyncio
async def test_download_with_token_configured_rejects_missing_header() -> None:
    cache = make_cache(token="secret")
    cache._cache["test.txt"] = b"data"
    with pytest.raises(web.HTTPUnauthorized):
        await cache.download_handler(make_request())


@pytest.mark.asyncio
async def test_download_with_token_configured_rejects_wrong_token() -> None:
    cache = make_cache(token="secret")
    cache._cache["test.txt"] = b"data"
    with pytest.raises(web.HTTPUnauthorized):
        await cache.download_handler(make_request({"Authorization": "Bearer wrong"}))


@pytest.mark.asyncio
async def test_download_with_token_configured_accepts_correct_token() -> None:
    cache = make_cache(token="secret")
    cache._cache["test.txt"] = b"data"
    response = await cache.download_handler(make_request({"Authorization": "Bearer secret"}))
    assert response.body == b"data"


@pytest.mark.asyncio
async def test_upload_with_token_configured_rejects_missing_header() -> None:
    cache = make_cache(token="secret")
    with pytest.raises(web.HTTPUnauthorized):
        await cache.upload_handler(make_request())


# ── CORS ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_download_response_has_cors_header() -> None:
    cache = make_cache()
    cache._cache["test.txt"] = b"data"
    response = await cache.download_handler(make_request())
    assert response.headers["Access-Control-Allow-Origin"] == "*"


@pytest.mark.asyncio
async def test_ping_response_has_cors_header() -> None:
    cache = make_cache()
    response = await cache.ping_handler(make_request())
    assert response.headers["Access-Control-Allow-Origin"] == "*"


@pytest.mark.asyncio
async def test_options_handler_returns_cors_preflight_headers() -> None:
    cache = make_cache()
    response = await cache.options_handler(make_request())
    assert response.headers["Access-Control-Allow-Origin"] == "*"
    assert response.headers["Access-Control-Allow-Methods"] == "GET"
    assert response.headers["Access-Control-Allow-Headers"] == "Authorization"
