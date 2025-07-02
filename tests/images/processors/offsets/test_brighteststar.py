import logging

import numpy as np
import pytest
from astropy.io import fits
from astropy.table import QTable
from astropy.utils.data import get_pkg_data_filename

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, OnSkyDistance
from pyobs.images.processors.offsets import BrightestStarOffsets


@pytest.mark.asyncio
async def test_missing_catalog(caplog: pytest.LogCaptureFixture) -> None:
    offsets = BrightestStarOffsets()
    image = Image()

    with caplog.at_level(logging.WARNING):
        await offsets(image)

    assert caplog.messages[0] == "No catalog found in image."


@pytest.mark.asyncio
async def test_empty_catalog(caplog: pytest.LogCaptureFixture) -> None:
    offsets = BrightestStarOffsets()
    image = Image(catalog=QTable())

    with caplog.at_level(logging.WARNING):
        await offsets(image)

    assert caplog.messages[0] == "No catalog found in image."


@pytest.mark.asyncio
async def test_call() -> None:
    fn = get_pkg_data_filename("data/j94f05bgq_flt.fits", package="astropy.wcs.tests")
    f = fits.open(fn)

    catalog = QTable({"x": [2050], "y": [1020], "flux": [1]})
    image = Image(data=np.zeros((20, 20)), catalog=catalog, header=f[1].header)

    offsets = BrightestStarOffsets()

    output_image = await offsets(image)
    pixel_offset = output_image.get_meta(PixelOffsets)

    assert pixel_offset.dx == 2.0
    assert pixel_offset.dy == -4.0

    on_sky_distance = output_image.get_meta(OnSkyDistance)
    np.testing.assert_almost_equal(on_sky_distance.distance.value, 6.06585686e-05)


@pytest.mark.asyncio
async def test_ordering() -> None:
    catalog = QTable({"x": [2050, 2049], "y": [1020, 1021], "flux": [1, 2]})

    assert BrightestStarOffsets._get_brightest_star_position(catalog) == (2049, 1021)
