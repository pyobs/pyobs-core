import numpy as np
import pytest

from pyobs.images.processors.photometry._photutil_aperture_photometry import _PhotUtilAperturePhotometry


@pytest.mark.asyncio
async def test_call_to_large_pixel_scale(caplog, const_test_image):
    photometry = _PhotUtilAperturePhotometry(const_test_image, [(40, 40)])

    await photometry(1)

    assert photometry.catalog.keys() == ["x", "y"]
    assert photometry.catalog["x"] == [40]
    assert photometry.catalog["y"] == [40]


@pytest.mark.asyncio
async def test_call_const(const_test_image):
    const_test_image.header["CD1_1"] = 1 / (2.5 * 3600)
    photometry = _PhotUtilAperturePhotometry(const_test_image, [(40, 40)])
    await photometry(1)

    # Test background is 1.0
    np.testing.assert_almost_equal(photometry.catalog[f"bkgaper1"][0], 1.0, 14)

    # Test flux is 0.0
    np.testing.assert_almost_equal(photometry.catalog[f"fluxaper1"][0], 0.0, 13)


@pytest.mark.asyncio
async def test_update_header_flux_error(const_test_image):
    photometry = _PhotUtilAperturePhotometry(const_test_image, [(40, 40)])

    test_array = np.array([1.0])
    photometry._update_header(1, test_array, test_array, test_array)
    np.testing.assert_array_equal(photometry.catalog["fluxerr1"], test_array)