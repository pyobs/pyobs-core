import io
from copy import copy

import astropy.table
import numpy as np
import numpy.testing
import pytest
from astropy.io import fits
from astropy.io.fits import ImageHDU, table_to_hdu

from pyobs.images import Image


@pytest.fixture()
def mock_image():
    return np.ones((4, 4))


def test_init_default():
    image = Image()

    assert image.data is None
    assert image.header == fits.Header()
    assert image.uncertainty is None
    assert image.mask is None
    assert image.catalog is None
    assert image.raw is None
    assert image.meta == {}


def test_init_values(mock_image):
    header = fits.Header()
    header["test"] = 1
    mask = np.zeros((4, 4))
    uncertainties = np.zeros((4, 4))
    catalog = astropy.table.Table(np.array([1]))
    raw = copy(mock_image)
    meta = {"test": 1}

    image = Image(mock_image, header, mask, uncertainties, catalog, raw, meta)

    np.testing.assert_array_equal(mock_image, image.data)
    np.testing.assert_array_equal(mask, image.mask)
    np.testing.assert_array_equal(uncertainties, image.uncertainty)
    np.testing.assert_array_equal(catalog.as_array(), image.catalog.as_array())
    np.testing.assert_array_equal(mock_image, image.raw)
    assert image.meta == meta

    assert isinstance(image.header, fits.Header)
    assert image.header["test"] == 1
    assert image.header["NAXIS1"] == 4
    assert image.header["NAXIS2"] == 4


def test_from_bytes(mock_image):
    hdu = fits.PrimaryHDU(mock_image)
    hdul = fits.HDUList([hdu])

    byte_fits = io.BytesIO()
    hdul.writeto(fileobj=byte_fits)

    image = Image.from_bytes(byte_fits.getvalue())

    np.testing.assert_array_equal(image.data, mock_image)


def test_from_file():
    assert False


def test_from_ccddata():
    assert False


def test__from_hdu_list_no_hdu():
    hdu = fits.PrimaryHDU(None)
    img_hdu = fits.ImageHDU(None)
    hdul = fits.HDUList([hdu])

    with pytest.raises(ValueError):
        Image._from_hdu_list(hdul)

    with pytest.raises(ValueError):
        Image._from_hdu_list(fits.HDUList())

    img_hdu.name = "NOT_SCI"

    with pytest.raises(ValueError):
        Image._from_hdu_list(fits.HDUList(img_hdu))

    hdu.name = "SCI"

    with pytest.raises(ValueError):
        Image._from_hdu_list(hdul)


def test__from_hdu_list_w_optionals(mock_image):
    hdu = fits.PrimaryHDU(mock_image)

    mask = fits.ImageHDU(np.zeros((4, 4)).astype(np.uint8))
    mask.name = "MASK"
    uncert = fits.ImageHDU(np.zeros((4, 4)).astype(np.uint8))
    uncert.name = "UNCERT"
    cat = table_to_hdu(astropy.table.Table(np.array([1])))
    cat.name = "CAT"
    raw = fits.ImageHDU(copy(mock_image).astype(np.uint8))
    raw.name = "RAW"

    hdul = fits.HDUList([hdu, mask, uncert, cat, raw])

    image = Image._from_hdu_list(hdul)

    np.testing.assert_array_equal(hdul["MASK"].data, image.mask)
    np.testing.assert_array_equal(hdul["UNCERT"].data, image.uncertainty)
    np.testing.assert_array_equal(hdul["CAT"].data, image.catalog.as_array())
    np.testing.assert_array_equal(mock_image, image.raw)


def test__from_hdu_list_non_optionals(mock_image):
    hdu = fits.PrimaryHDU(mock_image)
    hdul = fits.HDUList([hdu])

    image = Image._from_hdu_list(hdul)

    np.testing.assert_array_equal(image.data, mock_image)
    assert image.header == hdu.header
    assert image.mask is None
    assert image.uncertainty is None
    assert image.catalog is None
    assert image.raw is None
    assert image.meta == {}


def test_unit():
    assert False


def test_copy():
    assert False


def test_writeto():
    assert False


def test_to_bytes():
    assert False


def test_write_catalog():
    assert False


def test_to_ccddata():
    assert False


def test_format_filename():
    assert False


def test_pixel_scale():
    assert False


def test_to_jpeg():
    assert False


def test_set_meta():
    assert False


def test_has_meta():
    assert False


def test_get_meta():
    assert False


def test_get_meta_safe():
    assert False
