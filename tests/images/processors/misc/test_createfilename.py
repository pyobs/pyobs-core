import pytest

import pyobs.utils.fits
from pyobs.images import Image
from pyobs.images.processors.misc import CreateFilename


def test_init_input(mocker):
    spy = mocker.spy(pyobs.utils.fits.FilenameFormatter, "__init__")
    CreateFilename("test")

    assert spy.call_args[0][1] == "test"


def test_init_default(mocker):
    spy = mocker.spy(pyobs.utils.fits.FilenameFormatter, "__init__")
    CreateFilename(None)

    assert (spy.call_args[0][1] ==
            "{SITEID}{TELID}-{INSTRUME}-{DAY-OBS|date:}-{FRAMENUM|string:04d}-{IMAGETYP|type}01.fits")


@pytest.mark.asyncio
async def test_call(mocker):
    mocker.patch("pyobs.images.Image.format_filename")

    create_filename = CreateFilename(None)
    image = Image()
    output_image = await create_filename(image)

    pyobs.images.Image.format_filename.assert_called_once_with(create_filename._formatter)
    assert image != output_image
