import logging
from typing import List, Tuple

import numpy as np
import pytest
from astropy.io.fits import Header
from astropy.table import QTable

from pyobs.images import Image
from pyobs.images.processors.photometry._photometry_calculator import _PhotometryCalculator
from pyobs.images.processors.photometry.aperture_photometry import AperturePhotometry


class MockPhotometryCalculator(_PhotometryCalculator):
    def __init__(self):
        self._catalog = None

    @property
    def catalog(self) -> QTable:
        return self._catalog

    def set_data(self, image: Image):
        self._catalog = image.catalog.copy()

    def __call__(self, diameter: int):
        self._catalog[f"call{diameter}"] = 1


@pytest.mark.asyncio
async def test_call_invalid_data(caplog):
    image = Image()
    photometry = AperturePhotometry(MockPhotometryCalculator())

    with caplog.at_level(logging.WARNING):
        result = await photometry(image)

    assert caplog.records[0].message == "No data found in image."
    assert result == image


@pytest.mark.asyncio
async def test_call_invalid_pixelscale(caplog):
    image = Image(data=np.zeros((1, 1)))
    photometry = AperturePhotometry(MockPhotometryCalculator())

    with caplog.at_level(logging.WARNING):
        result = await photometry(image)

    assert caplog.records[0].message == "No pixel scale provided by image."
    assert result == image


@pytest.mark.asyncio
async def test_call_invalid_catalog(caplog):
    image = Image(data=np.zeros((1, 1)), header=Header({"CD1_1": 1.0}))
    photometry = AperturePhotometry(MockPhotometryCalculator())

    with caplog.at_level(logging.WARNING):
        result = await photometry(image)

    assert caplog.records[0].message == "No catalog found in image."
    assert result == image


@pytest.mark.asyncio
async def test_call_valid(const_test_image):
    calculator = MockPhotometryCalculator()
    photometry = AperturePhotometry(calculator)
    result = await photometry(const_test_image)

    assert all([f"call{x}" in result.catalog.keys() for x in AperturePhotometry.APERTURE_RADII])

    np.testing.assert_array_equal(const_test_image.data, result.data)
    assert const_test_image.catalog is not result.catalog
