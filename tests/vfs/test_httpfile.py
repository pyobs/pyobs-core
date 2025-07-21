import aiohttp
import pytest
from _pytest.monkeypatch import MonkeyPatch

from pyobs.vfs import HttpFile


class Response:
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content


uploaded = None


class Session:
    def mount(self, *args, **kwargs):
        pass

    def get(self, url, params=None, **kwargs):  # noqa: F824
        return Response(200, uploaded)

    def post(self, url, data=None, json=None, **kwargs):  # noqa: F824
        global uploaded
        uploaded = data
        return Response(200, None)


@pytest.mark.asyncio
async def test_upload_download(monkeypatch: MonkeyPatch) -> None:
    # mock it
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: Session())

    # create config
    upload = "http://localhost:37075/"
    download = "http://localhost:37075/"

    # test data
    test = "Hello world"

    # write file
    async with HttpFile("test.txt", "w", upload=upload, download=download) as f:
        await f.write(test)

    # read data
    async with HttpFile("test.txt", "r", upload=upload, download=download) as f:
        assert test == await f.read()
