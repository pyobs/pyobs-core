import logging

import numpy as np
import pytest
from astropy.table import QTable

from pyobs.images import Image
from pyobs.images.processors.photometry import SepPhotometry


@pytest.fixture()
def test_catalog():
    catalog = QTable({"x": [40], "y": [40], "a": [10], "b": [5], "kronrad": [5]})
    return catalog


@pytest.mark.asyncio
async def test_call_invalid_data(caplog):
    image = Image()
    photometry = SepPhotometry()

    with caplog.at_level(logging.WARNING):
        result = await photometry(image)

    assert caplog.records[0].message == "No data found in image."
    assert result == image


@pytest.mark.asyncio
async def test_call_invalid_pixelscale(caplog, test_catalog):
    const_test_image = Image(data=np.ones((100, 100)), catalog=test_catalog)
    photometry = SepPhotometry()

    with caplog.at_level(logging.WARNING):
        result = await photometry(const_test_image)

    assert caplog.records[0].message == "No pixel scale provided by image."
    assert result == const_test_image



@pytest.mark.asyncio
async def test_call_invalid_catalog(caplog):
    image = Image(data=np.zeros((100, 100)))
    image.header["CD1_1"] = 1/(2.5*3600)
    photometry = SepPhotometry()

    with caplog.at_level(logging.WARNING):
        result = await photometry(image)

    assert caplog.records[0].message == "No catalog found in image."
    assert result == image


@pytest.mark.asyncio
async def test_call_const(test_catalog):
    const_test_image = Image(data=np.ones((100, 100)), catalog=test_catalog)
    photometry = SepPhotometry()
    const_test_image.header["CD1_1"] = 1/(2.5*3600)
    result = await photometry(const_test_image)

    # Test background is 1.0
    np.testing.assert_almost_equal(result.catalog["background"][0], 1.0, 14)

    # Test flux is 0.0
    assert all([
        abs(result.catalog[f"fluxaper{diameter}"][0] - 0.0) < 1e-13
        for diameter in range(1, 9)
    ])

    assert all([
        abs(result.catalog[f"fluxerr{diameter}"][0] - 0.0) < 1e-13
        for diameter in range(1, 9)
    ])


@pytest.mark.asyncio
async def test_call_single_peak(test_catalog):
    data = np.zeros((100, 100))
    data[39][39] = 100
    const_test_image = Image(data=data, catalog=test_catalog)
    photometry = SepPhotometry()
    const_test_image.header["CD1_1"] = 1/(2.5*3600)
    result = await photometry(const_test_image)

    # Test background is 0.0
    np.testing.assert_almost_equal(result.catalog["background"][0], 0.0, 14)

    # Test flux is 100.0
    assert all([
        abs(result.catalog[f"fluxaper{diameter}"][0] - 100.0) < 1e-13
        for diameter in range(1, 9)
    ])

    assert all([
        abs(result.catalog[f"fluxerr{diameter}"][0] - 0.0) < 1e-13
        for diameter in range(1, 9)
    ])

