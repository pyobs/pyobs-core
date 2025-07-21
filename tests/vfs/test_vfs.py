import os
import pytest

from pyobs.vfs import VirtualFileSystem


@pytest.mark.asyncio
async def test_read_file():
    # create config
    roots = {"local": {"class": "pyobs.vfs.LocalFile", "root": os.path.dirname(__file__)}}

    # create vfs
    vfs = VirtualFileSystem(roots=roots)

    # open file
    filename = "/local/" + os.path.basename(__file__)
    async with vfs.open_file(filename, "r") as f:
        assert await f.read(9) == "import os"
