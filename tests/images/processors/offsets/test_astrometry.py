import numpy as np
import pytest
from astropy.io import fits
from astropy.utils.data import get_pkg_data_filename

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, OnSkyDistance
from pyobs.images.processors.offsets import AstrometryOffsets


@pytest.mark.asyncio
async def test_call() -> None:
    filename = get_pkg_data_filename("data/j94f05bgq_flt.fits", package="astropy.wcs.tests")
    fits_file = fits.open(filename)
    header = fits_file[1].header
    header["TEL-RA"] = 5.63
    header["TEL-DEC"] = -72.05

    image = Image(header=header)

    offsets = AstrometryOffsets()

    output_image = await offsets(image)
    pixel_offset = output_image.get_meta(PixelOffsets)

    np.testing.assert_almost_equal(pixel_offset.dx, 128.94120449972797)
    np.testing.assert_almost_equal(pixel_offset.dy, -309.1795167877043)

    on_sky_distance = output_image.get_meta(OnSkyDistance)
    np.testing.assert_almost_equal(on_sky_distance.distance.value, 0.004575193216279022)
