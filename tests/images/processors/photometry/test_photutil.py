import logging

import numpy as np
import pytest
from astropy.io.fits import Header
from astropy.table import QTable

from pyobs.images import Image
from pyobs.images.processors.photometry import PhotUtilsPhotometry


@pytest.fixture()
def const_test_image() -> Image:
    data = np.ones((100, 100))
    header = Header({"CD1_1": 1.0})
    catalog = QTable({"x": [40.0], "y": [40.0]})
    return Image(data=data, header=header, catalog=catalog)


@pytest.mark.asyncio
async def test_call_invalid_pixelscale(caplog):
    image = Image()
    photometry = PhotUtilsPhotometry()

    with caplog.at_level(logging.WARNING):
        result = await photometry(image)

    assert caplog.records[0].message == "No pixel scale provided by image."
    assert result == image


@pytest.mark.asyncio
async def test_call_invalid_catalog(caplog):
    image = Image(header=Header({"CD1_1": 1.0}))
    photometry = PhotUtilsPhotometry()

    with caplog.at_level(logging.WARNING):
        result = await photometry(image)

    assert caplog.records[0].message == "No catalog in image."
    assert result == image


@pytest.mark.asyncio
async def test_call_to_large_pixel_scale(caplog, const_test_image):
    photometry = PhotUtilsPhotometry()

    result = await photometry(const_test_image)

    assert result.catalog.keys() == ["x", "y"]
    assert result.catalog["x"] == [40]
    assert result.catalog["y"] == [40]


@pytest.mark.asyncio
async def test_call_const(caplog, const_test_image):
    photometry = PhotUtilsPhotometry()
    const_test_image.header["CD1_1"] = 1/(2.5*3600)
    result = await photometry(const_test_image)

    # Test background is 1.0
    assert all([
        abs(result.catalog[f"bkgaper{diameter}"][0] - 1.0) < 1e-14
        for diameter in range(1, 9)
    ])

    # Test flux is 0.0
    assert all([
        abs(result.catalog[f"fluxaper{diameter}"][0] - 0.0) < 1e-13
        for diameter in range(1, 9)
    ])
