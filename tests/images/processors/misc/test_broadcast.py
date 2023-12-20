import pytest

import pyobs.utils.fits
from pyobs.comm import Comm
from pyobs.events import NewImageEvent
from pyobs.images import Image
from pyobs.images.processors.misc import Broadcast
from pyobs.utils.enums import ImageType
from pyobs.vfs import VirtualFileSystem


def test_init(mocker):
    mocker.patch("pyobs.utils.fits.FilenameFormatter.__init__", return_value=None)
    Broadcast()

    pyobs.utils.fits.FilenameFormatter.__init__.assert_called_once_with("/cache/processed_{ORIGNAME}")


@pytest.mark.asyncio
async def test_open(mocker):
    broadcast = Broadcast()
    broadcast.comm = Comm()

    mocker.patch.object(broadcast.comm, "register_event")

    await broadcast.open()
    broadcast.comm.register_event.assert_called_once_with(NewImageEvent)


@pytest.mark.asyncio
async def test_call(mocker):
    image = Image()
    image.header["IMAGETYP"] = "object"
    mocker.patch.object(image, "format_filename", return_value="image.fits")

    broadcast = Broadcast()
    broadcast.comm = Comm()
    mocker.patch.object(broadcast.comm, "send_event")
    broadcast.vfs = VirtualFileSystem()
    mocker.patch.object(broadcast.vfs, "write_image")

    await broadcast(image)

    broadcast.vfs.write_image.assert_called_once_with("image.fits", image)

    image_event = broadcast.comm.send_event.call_args[0][0]

    assert image_event.data["filename"] == "image.fits"
    assert image_event.data["image_type"] == "object"
