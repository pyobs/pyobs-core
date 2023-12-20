import logging

import numpy as np
import pytest

from pyobs.images import Image
from pyobs.images.processors.misc import AddMask


def test_init_array():
    mask = np.zeros((2, 2))
    masks = {"camera": {"1x1": mask}}

    adder = AddMask(masks)

    np.testing.assert_array_equal(adder._masks["camera"]["1x1"], mask)


def test_init_str(mocker):
    mask = np.zeros((2, 2))
    mask_file = "maskfile.fits"

    mocker.patch("astropy.io.fits.getdata", return_value=mask)

    masks = {"camera": {"1x1": mask_file}}
    adder = AddMask(masks)

    np.testing.assert_array_equal(adder._masks["camera"]["1x1"], mask)


def test_init_invalid():
    masks = {"camera": {"1x1": 1}}

    with pytest.raises(ValueError):
        AddMask(masks)


@pytest.mark.asyncio
async def test_call():
    mask = np.zeros((2, 2))
    masks = {"camera": {"1x1": mask}}

    image = Image()
    image.header["INSTRUME"] = "camera"
    image.header["XBINNING"] = 1
    image.header["YBINNING"] = 1

    adder = AddMask({})
    adder._masks = masks

    output_image = await adder(image)
    np.testing.assert_array_equal(output_image.mask, mask)


@pytest.mark.asyncio
async def test_call_invalid(caplog):
    image = Image()
    image.header["INSTRUME"] = "camera"
    image.header["XBINNING"] = 1
    image.header["YBINNING"] = 1

    adder = AddMask({})
    with caplog.at_level(logging.WARNING):
        await adder(image)

    assert caplog.records[0].message == "No mask found for binning of frame."
