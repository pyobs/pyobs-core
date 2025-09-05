import pytest
from aioresponses import aioresponses

from pyobs.vfs import HttpFile


uploaded = None


@pytest.fixture
def mocked():
    with aioresponses() as m:
        yield m


@pytest.mark.asyncio
async def test_upload_download(mocked) -> None:
    # create config
    upload = "http://localhost:37075/test.txt"
    download = "http://localhost:37075/test.txt"

    # test data
    test = "Hello world"

    # mock
    mocked.post(upload, status=200)
    mocked.get(download, status=200, body=test)

    # write file
    async with HttpFile("test.txt", "w", upload=upload, download=download) as f:
        await f.write(test)

    # read data
    async with HttpFile("test.txt", "r", upload=upload, download=download) as f:
        assert test == (await f.read()).decode()
