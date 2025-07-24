import pytest

from pyobs.vfs import MemoryFile


@pytest.mark.asyncio
async def test_memfile():
    async with MemoryFile("test.txt", "w") as f:
        await f.write("Hello world!")

    async with MemoryFile("test.txt", "r") as f:
        assert "Hello world!" == await f.read()
