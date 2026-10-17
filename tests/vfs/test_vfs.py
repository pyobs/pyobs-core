import os

import pytest

from pyobs.vfs import UnknownRootError, VirtualFileSystem


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
    with pytest.raises(UnknownRootError, match="old"):
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


def test_unknown_root_open_file_raises_unknown_root_error() -> None:
    vfs = VirtualFileSystem()
    with pytest.raises(UnknownRootError) as exc:
        vfs.open_file("/nope/x.fits", "r")
    assert isinstance(exc.value, ValueError)
    assert exc.value.root == "nope"
    assert exc.value.path == "/nope/x.fits"
    assert str(exc.value).startswith("Could not find root nope")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method, args",
    [
        ("read_fits", ()),
        ("write_fits", (None,)),
        ("read_image", ()),
        ("write_image", (None,)),
        ("write_bytes", (b"",)),
        ("read_csv", ()),
        ("write_csv", (None,)),
        ("read_yaml", ()),
        ("write_yaml", ({},)),
        ("local_path", ()),
        ("find", ("*",)),
        ("listdir", ()),
        ("exists", ()),
        ("remove", ()),
        ("rmdir", ()),
    ],
)
async def test_unknown_root_raises_from_all_entry_points(method: str, args: tuple) -> None:
    vfs = VirtualFileSystem()
    with pytest.raises(UnknownRootError) as exc:
        await getattr(vfs, method)("/nope/x", *args)
    assert not isinstance(exc.value, KeyError)
    assert exc.value.root == "nope"


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["exists", "listdir"])
async def test_path_without_root_is_plain_value_error(method: str) -> None:
    vfs = VirtualFileSystem()
    with pytest.raises(ValueError) as exc:
        vfs.open_file("x.fits", "r")
    assert not isinstance(exc.value, UnknownRootError)
    with pytest.raises(ValueError) as exc:
        await getattr(vfs, method)("x.fits")
    assert not isinstance(exc.value, UnknownRootError)


@pytest.mark.asyncio
async def test_known_root_exists_and_listdir(tmp_path) -> None:
    (tmp_path / "a.txt").write_text("x")
    vfs = VirtualFileSystem(roots={"tmp": {"class": "pyobs.vfs.LocalFile", "root": str(tmp_path)}})
    assert await vfs.exists("/tmp/a.txt")
    assert not await vfs.exists("/tmp/b.txt")
    assert "a.txt" in await vfs.listdir("/tmp/")
    assert await vfs.local_path("/tmp/a.txt") == str(tmp_path / "a.txt")
