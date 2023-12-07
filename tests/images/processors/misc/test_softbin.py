import logging

import numpy as np
import pytest
from astropy.io.fits import Header

from pyobs.images import Image
from pyobs.images.processors.misc import SoftBin


def test_init_default():
    binner = SoftBin()

    assert binner.binning == 2


@pytest.mark.asyncio
async def test_call_invalid(caplog):
    image = Image()
    binner = SoftBin()

    with caplog.at_level(logging.WARNING):
        await binner(image)

    assert caplog.records[0].message == "No data found in image."


@pytest.mark.asyncio
async def test_call():
    header = Header({"CRPIX1": 8, "CRPIX2": 8,
              "DET-BIN1": 1, "DET-BIN2": 1, "XBINNING": 1, "YBINNING": 1, "CDELT1": 1, "CDELT2": 1})

    image = Image(data=np.zeros((16, 16)), header=header)
    binner = SoftBin(binning=4)

    result_image = await binner(image)
    assert np.shape(result_image.data) == (4, 4)

    assert result_image.header["NAXIS2"] == 4
    assert result_image.header["NAXIS2"] == 4

    assert result_image.header["CRPIX1"] == 2
    assert result_image.header["CRPIX1"] == 2

    assert all([result_image.header[key] == 4 for key in ["DET-BIN1", "DET-BIN2", "XBINNING", "YBINNING", "CDELT1", "CDELT2"]])