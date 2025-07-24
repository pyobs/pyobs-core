import os
from pathlib import Path

import pytest

from pyobs.vfs import LocalFile

"""
@pytest.mark.asyncio
async def test_read_file() -> None:
    # create config
    root = os.path.dirname(__file__)

    # open file
    filename = os.path.basename(__file__)
    async with LocalFile(filename, "r", root=root) as f:
        assert f.readline() == b"import os" + bytes(os.linesep, "utf-8")
"""


@pytest.mark.asyncio
async def test_file_not_found() -> None:
    # create config
    root = os.path.dirname(__file__)

    # open file
    with pytest.raises(FileNotFoundError):
        async with LocalFile("doesnt_exist.txt", "r", root=root):
            pass


@pytest.mark.asyncio
async def test_invalid_path() -> None:
    # create config
    root = os.path.dirname(__file__)

    # open file
    with pytest.raises(ValueError):
        async with LocalFile("../test.txt", "r", root=root):
            pass

    # open file
    with pytest.raises(ValueError):
        async with LocalFile("/test.txt", "r", root=root):
            pass


@pytest.mark.asyncio
async def test_write_file(tmp_path: Path) -> None:
    # create config
    root = str(tmp_path)

    # open file for write
    async with LocalFile("test.txt", "w", root=root) as f:
        await f.write("This is a test")

    # test it
    assert tmp_path.joinpath("test.txt").read_text() == "This is a test"


@pytest.mark.asyncio
async def test_create_dir(tmp_path: Path) -> None:
    # create config
    root = str(tmp_path)

    # open file for write
    async with LocalFile("sub/test.txt", "w", root=root) as f:
        await f.write("This is a test")

    # test it
    assert tmp_path.joinpath("sub/test.txt").read_text() == "This is a test"

    # this should throw an exception
    with pytest.raises(ValueError):
        async with LocalFile("sub2/test.txt", "w", root=root, mkdir=False) as f:
            await f.write("This is a test")
