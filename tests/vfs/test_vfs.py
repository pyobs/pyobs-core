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


def test_default_roots() -> None:
    vfs = VirtualFileSystem()
    assert set(vfs._roots) == {"pyobs", "robotic"}


@pytest.mark.asyncio
async def test_set_roots_replaces_roots_and_keeps_defaults() -> None:
    vfs = VirtualFileSystem(roots={"old": {"class": "pyobs.vfs.LocalFile", "root": "/tmp"}})
    vfs.set_roots({"local": {"class": "pyobs.vfs.LocalFile", "root": os.path.dirname(__file__)}})

    assert set(vfs._roots) == {"pyobs", "robotic", "local"}
    with pytest.raises(ValueError, match="old"):
        vfs.open_file("/old/x", "r")
    async with vfs.open_file("/local/" + os.path.basename(__file__), "r") as f:
        assert await f.read(9) == "import os"


def test_set_roots_can_override_defaults() -> None:
    vfs = VirtualFileSystem()
    vfs.set_roots({"pyobs": {"class": "pyobs.vfs.LocalFile", "root": "/somewhere/else/"}})
    assert vfs._roots["pyobs"]["root"] == "/somewhere/else/"
    assert "robotic" in vfs._roots


def test_set_roots_without_argument_resets_to_defaults() -> None:
    vfs = VirtualFileSystem(roots={"local": {"class": "pyobs.vfs.LocalFile", "root": "/tmp"}})
    vfs.set_roots()
    assert set(vfs._roots) == {"pyobs", "robotic"}


def test_set_roots_does_not_mutate_the_old_dict() -> None:
    vfs = VirtualFileSystem()
    old = vfs._roots
    vfs.set_roots({"local": {"class": "pyobs.vfs.LocalFile", "root": "/tmp"}})
    assert set(old) == {"pyobs", "robotic"}
