from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pyobs.vfs import HttpFile


def _make_response(status: int = 200, body: bytes = b"") -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.read = AsyncMock(return_value=body)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


def _make_session(post_resp: MagicMock, get_resp: MagicMock) -> MagicMock:
    session = MagicMock()
    session.post = MagicMock(return_value=post_resp)
    session.get = MagicMock(return_value=get_resp)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


@pytest.mark.asyncio
async def test_upload_download() -> None:
    upload = "http://localhost:37075/test.txt"
    download = "http://localhost:37075/test.txt"
    test = "Hello world"

    post_resp = _make_response(200)
    get_resp = _make_response(200, body=test.encode())
    session = _make_session(post_resp, get_resp)

    with patch("aiohttp.ClientSession", return_value=session):
        async with HttpFile("test.txt", "w", upload=upload, download=download) as f:
            await f.write(test)

        async with HttpFile("test.txt", "r", upload=upload, download=download) as f:
            assert test == (await f.read()).decode()
