import os
import pytest

from pyobs.vfs import TempFile


@pytest.mark.asyncio
async def test_write_file() -> None:
    # create new temp file with name
    async with TempFile(mode="w") as f:
        filename = f.full_name
        # does file exist?
        assert os.path.exists(filename)

    # file should be gone
    assert not os.path.exists(filename)


@pytest.mark.asyncio
async def test_name() -> None:
    # test prefix
    async with TempFile(mode="w", prefix="test") as f:
        assert f.full_name.startswith("test")

    # test suffix
    async with TempFile(mode="w", suffix=".fits") as f:
        assert f.full_name.endswith(".fits")

    # test given name
    async with TempFile(name="test.txt", mode="w") as f:
        assert f.full_name == "test.txt"
