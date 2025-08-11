import pytest

import pyobs.utils.fits
from pyobs.comm import Comm
from pyobs.events import NewImageEvent
from pyobs.images import Image
from pyobs.images.processors.image import Save
from pyobs.vfs import VirtualFileSystem


def test_init(mocker):
    mocker.patch("pyobs.utils.fits.FilenameFormatter.__init__", return_value=None)
    Save()

    pyobs.utils.fits.FilenameFormatter.__init__.assert_called_once_with("/pyobs/image.fits")


@pytest.mark.asyncio
async def test_open(mocker):
    save = Save(broadcast=True)
    save.comm = Comm()

    mocker.patch.object(save.comm, "register_event")

    await save.open()
    save.comm.register_event.assert_called_once_with(NewImageEvent)


@pytest.mark.asyncio
async def test_call(mocker):
    image = Image()
    image.header["IMAGETYP"] = "object"
    mocker.patch.object(image, "format_filename", return_value="image.fits")

    save = Save()
    save.comm = Comm()
    mocker.patch.object(save.comm, "send_event")
    save.vfs = VirtualFileSystem()
    mocker.patch.object(save.vfs, "write_image")

    await save(image)

    save.vfs.write_image.assert_called_once_with("image.fits", image)

    # todo: fix
    # image_event = save.comm.send_event.call_args[0][0]
    #
    # assert image_event.data["filename"] == "image.fits"
    # assert image_event.data["image_type"] == "object"
