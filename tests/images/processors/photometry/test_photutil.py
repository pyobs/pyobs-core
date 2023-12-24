import logging

import numpy as np
import pytest
from astropy.io.fits import Header

import pyobs.images.processors.photometry._photutil_aperture_photometry
from pyobs.images import Image
from pyobs.images.processors.photometry import PhotUtilsPhotometry

@pytest.mark.asyncio
async def test_call_invalid_data(caplog):
    image = Image()
    photometry = PhotUtilsPhotometry()

    with caplog.at_level(logging.WARNING):
        result = await photometry(image)

    assert caplog.records[0].message == "No data found in image."
    assert result == image


@pytest.mark.asyncio
async def test_call_invalid_pixelscale(caplog):
    image = Image(data=np.zeros((1, 1)))
    photometry = PhotUtilsPhotometry()

    with caplog.at_level(logging.WARNING):
        result = await photometry(image)

    assert caplog.records[0].message == "No pixel scale provided by image."
    assert result == image


@pytest.mark.asyncio
async def test_call_invalid_catalog(caplog):
    image = Image(data=np.zeros((1,1)), header=Header({"CD1_1": 1.0}))
    photometry = PhotUtilsPhotometry()

    with caplog.at_level(logging.WARNING):
        result = await photometry(image)

    assert caplog.records[0].message == "No catalog found in image."
    assert result == image


@pytest.mark.asyncio
async def test_call(mocker, const_test_image):
    mocker.patch("pyobs.images.processors.photometry._photutil_aperture_photometry._PhotUtilAperturePhotometry.__call__")

    photometry = PhotUtilsPhotometry()
    await photometry(const_test_image)

    pyobs.images.processors.photometry._photutil_aperture_photometry._PhotUtilAperturePhotometry.__call__.assert_called()

    assert pyobs.images.processors.photometry._photutil_aperture_photometry._PhotUtilAperturePhotometry.__call__.call_count == 8