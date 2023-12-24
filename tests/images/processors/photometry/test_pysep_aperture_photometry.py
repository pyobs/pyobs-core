import numpy as np
import pytest
from astropy.table import QTable

from pyobs.images import Image
from pyobs.images.processors.photometry._sep_aperture_photometry import _SepAperturePhotometry


@pytest.fixture()
def test_catalog():
    catalog = QTable({"x": [40], "y": [40], "a": [10], "b": [5], "kronrad": [5]})
    return catalog


@pytest.mark.asyncio
async def test_call_const(test_catalog):
    const_test_image = Image(data=np.ones((100, 100)), catalog=test_catalog)
    photometry = _SepAperturePhotometry()
    const_test_image.header["CD1_1"] = 1/(2.5*3600)

    photometry.set_data(const_test_image, [(40, 40)])
    photometry(5)

    # Test background is 1.0
    np.testing.assert_almost_equal(photometry.catalog["background"][0], 1.0, 14)

    # Test flux is 0.0
    assert abs(photometry.catalog[f"fluxaper5"][0] - 0.0) < 1e-13
    assert abs(photometry.catalog[f"fluxerr5"][0] - 0.0) < 1e-13


@pytest.mark.asyncio
async def test_call_single_peak(test_catalog):
    data = np.zeros((100, 100))
    data[39][39] = 100
    const_test_image = Image(data=data, catalog=test_catalog)
    photometry = _SepAperturePhotometry()
    const_test_image.header["CD1_1"] = 1/(2.5*3600)
    photometry.set_data(const_test_image, [(40, 40)])
    photometry(5)

    # Test background is 0.0
    np.testing.assert_almost_equal(photometry.catalog["background"][0], 0.0, 14)

    # Test flux is 100.0
    assert abs(photometry.catalog[f"fluxaper5"][0] - 100.0) < 1e-13
    assert abs(photometry.catalog[f"fluxerr5"][0] - 0.0) < 1e-13


