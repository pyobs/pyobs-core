import io
from copy import copy

import PIL.Image
import astropy.nddata
import astropy.table
import numpy as np
import pytest
from astropy.io import fits
from astropy.io.fits import table_to_hdu

import pyobs
from pyobs.images import Image


def assert_array_equal_or_none(check_value, value):
    if check_value is None:
        assert value is None
    else:
        np.testing.assert_array_equal(value, check_value)


def assert_equal_image_params(image, data=None, mask=None, uncertainty=None, catalog=None, raw=None, meta={}):
    assert_array_equal_or_none(data, image.data)
    assert_array_equal_or_none(mask, image.mask)
    assert_array_equal_or_none(uncertainty, image.uncertainty)

    if catalog is None:
        assert image.catalog is None
    else:
        assert_array_equal_or_none(catalog.as_array(), image.catalog.as_array())
    assert_array_equal_or_none(raw, image.raw)
    assert image.meta == meta


def assert_equal_image(image, other):
    assert_equal_image_params(image, other.data, other.mask, other.uncertainty, other.catalog, other.raw, other.meta)


@pytest.fixture()
def mock_image():
    return np.ones((4, 4))


def test_init_default():
    image = Image()

    assert_equal_image_params(image)
    assert image.header == fits.Header()


def test_init_values(mock_image):
    header = fits.Header()
    header["test"] = 1
    mask = np.zeros((4, 4))
    uncertainties = np.zeros((4, 4))
    catalog = astropy.table.Table(np.array([1]))
    raw = copy(mock_image)
    meta = {"test": 1}

    image = Image(mock_image, header, mask, uncertainties, catalog, raw, meta)

    assert_equal_image_params(image, mock_image, mask, uncertainties, catalog, raw, meta)

    assert isinstance(image.header, fits.Header)
    assert image.header["test"] == 1
    assert image.header["NAXIS1"] == 4
    assert image.header["NAXIS2"] == 4


def test_from_bytes(mocker, mock_image):
    hdu = fits.PrimaryHDU(mock_image)
    hdul = fits.HDUList([hdu])

    mocker.patch("pyobs.images.Image._from_hdu_list", return_value=Image(mock_image))

    byte_fits = io.BytesIO()
    hdul.writeto(fileobj=byte_fits)

    image = Image.from_bytes(byte_fits.getvalue())

    pyobs.images.Image._from_hdu_list.assert_called_once()
    np.testing.assert_array_equal(image.data, mock_image)


def test_from_file(mocker, mock_image):
    hdu = fits.PrimaryHDU(mock_image)
    hdul = fits.HDUList([hdu])

    mocker.patch("pyobs.images.Image._from_hdu_list", return_value=Image(mock_image))
    mocker.patch("astropy.io.fits.open", return_value=hdul)

    image = Image.from_file("test.fits")

    astropy.io.fits.open.assert_called_once_with("test.fits", memmap=False, lazy_load_hdus=False)
    pyobs.images.Image._from_hdu_list.assert_called_once_with(hdul)
    np.testing.assert_array_equal(image.data, mock_image)


def test_from_ccddata_w_values(mock_image):
    header = fits.Header()
    header["test"] = 1
    mask = np.zeros((4, 4))
    uncertainties = np.zeros((4, 4))
    ccd_data = astropy.nddata.CCDData(data=mock_image, header=header, mask=mask, uncertainty=uncertainties, unit='adu')

    image = Image.from_ccddata(ccd_data)

    assert_equal_image_params(image, mock_image, mask, uncertainties)
    assert image.header["test"] == 1


def test_from_ccddata_non_values(mock_image):
    header = fits.Header()
    header["test"] = 1

    ccd_data = astropy.nddata.CCDData(data=mock_image, header=header, unit='adu')

    image = Image.from_ccddata(ccd_data)
    assert_equal_image_params(image, mock_image)


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

    assert_equal_image_params(image, mock_image)
    assert image.header == hdu.header


def test_unit_w_value():
    header = fits.Header({"BUNIT": "TEST"})

    image = Image(header=header)
    assert image.unit == "test"


def test_unit_non_value():
    header = fits.Header({})

    image = Image(header=header)
    assert image.unit == "adu"


def test__deepcopy__(mocker):
    image = Image()
    mocker.patch("pyobs.images.Image.copy", return_value=image)

    assert image.__deepcopy__() == image
    pyobs.images.Image.copy.assert_called_once()


def test_copy(mock_image):
    header = fits.Header()
    header["test"] = 1
    mask = np.zeros((4, 4))
    uncertainties = np.zeros((4, 4))
    catalog = astropy.table.Table(np.array([1]))
    raw = copy(mock_image)
    meta = {"test": 1}

    original_image = Image(mock_image, header, mask, uncertainties, catalog, raw, meta)
    image = original_image.copy()

    assert_equal_image(image, original_image)

    assert isinstance(image.header, fits.Header)
    assert image.header["test"] == 1


def test__truediv__invalid(mock_image):
    other_image = Image()
    image = Image(mock_image)

    with pytest.raises(ValueError):
        image / other_image

    with pytest.raises(ValueError):
        other_image / other_image

    with pytest.raises(ValueError):
        other_image / image


def test__truediv__valid(mock_image):
    image = Image(mock_image * 4)
    other_image = Image(mock_image * 2)

    div_image = image / other_image

    np.testing.assert_array_equal(div_image.data, mock_image * 2)


def test_writeto_non_value(mock_image):
    """
    Testing against from bytes.
    Header value is not tested, because a valid header is needed.
    """
    byte_fits = io.BytesIO()
    original_image = Image(mock_image)
    original_image.writeto(byte_fits)

    image = Image.from_bytes(byte_fits.getvalue())

    assert_equal_image(image, original_image)


def test_writeto_w_value(mock_image):
    mask = np.zeros((4, 4))
    uncertainties = np.zeros((4, 4))
    catalog = astropy.table.Table(np.array([1]))
    raw = copy(mock_image)

    byte_fits = io.BytesIO()
    original_image = Image(mock_image, mask=mask, uncertainty=uncertainties, catalog=catalog, raw=raw)
    original_image.writeto(byte_fits)

    image = Image.from_bytes(byte_fits.getvalue())

    assert_equal_image(image, original_image)


def test_to_bytes(mock_image):
    mask = np.zeros((4, 4))
    uncertainties = np.zeros((4, 4))
    catalog = astropy.table.Table(np.array([1]))
    raw = copy(mock_image)

    original_image = Image(mock_image, mask=mask, uncertainty=uncertainties, catalog=catalog, raw=raw)
    byte_fits = original_image.to_bytes()

    image = Image.from_bytes(byte_fits)
    assert_equal_image(image, original_image)


def test_write_catalog_value(mocker):
    mocker.patch("astropy.io.fits.convenience.table_to_hdu")
    mocker.patch("astropy.io.fits.HDUList.writeto")
    catalog = astropy.table.Table(np.array([1]))
    image = Image(catalog=catalog)

    image.write_catalog("test.fits")
    # FIXME: Assertion does not work for some reason
    # astropy.io.fits.convenience.table_to_hdu.assert_called_once()
    astropy.io.fits.HDUList.writeto.assert_called_once()


def test_write_catalog_non_value(mocker):
    mocker.patch("astropy.io.fits.convenience.table_to_hdu")
    mocker.patch("astropy.io.fits.HDUList.writeto")

    image = Image()
    image.write_catalog("test.fits")

    astropy.io.fits.convenience.table_to_hdu.assert_not_called()
    astropy.io.fits.HDUList.writeto.assert_not_called()


def test_to_ccddata(mock_image):
    mask = np.zeros((4, 4))
    uncertainties = np.zeros((4, 4))

    original_image = Image(mock_image, mask=mask, uncertainty=uncertainties)
    ccd_data = original_image.to_ccddata()
    image = Image.from_ccddata(ccd_data)

    assert_equal_image(image, original_image)


def test_format_filename():
    formatter = lambda _: 1
    image = Image()

    assert "1" == image.format_filename(formatter)
    assert image.header["FNAME"] == 1


def test_pixel_scale():
    header = fits.Header()

    image = Image(header=header)
    assert image.pixel_scale is None

    image.header["CD1_1"] = 1.0
    assert image.pixel_scale == 3600.0

    image.header["CDELT1"] = 1.0
    assert image.pixel_scale == 3600.0


def test_to_jpeg_no_data():
    image = Image()

    with pytest.raises(ValueError):
        image.to_jpeg()


def test_to_jpeg_w_data(mocker, mock_image):
    image = Image(mock_image)

    spy = mocker.spy(PIL.Image, "fromarray")

    jpeg_image = image.to_jpeg()
    assert isinstance(jpeg_image, bytes)

    data = (0 * mock_image).astype(np.uint8)

    np.testing.assert_array_equal(spy.spy_return, data)


def test_to_jpeg_w_vmin(mocker, mock_image):
    image = Image(mock_image)

    spy = mocker.spy(PIL.Image, "fromarray")

    jpeg_image = image.to_jpeg(0.5, 1.5)
    assert isinstance(jpeg_image, bytes)

    data = (255/2 * mock_image).astype(np.uint8)

    np.testing.assert_array_equal(spy.spy_return, data)


def test_set_meta():
    image = Image()
    data: int = 1

    image.set_meta(data)
    assert image.meta[int] == 1


def test_has_meta():
    image = Image()

    assert image.has_meta(int) is False

    image.meta[int] = 1
    assert image.has_meta(int) is True


def test_get_meta_valid():
    image = Image()
    image.meta[int] = 1

    assert image.get_meta(int) == 1


def test_get_meta_invalid():
    image = Image()

    with pytest.raises(ValueError):
        image.get_meta(int)


def test_get_meta_wrong_type():
    image = Image()
    image.meta[int] = 1.0

    with pytest.raises(ValueError):
        image.get_meta(int)


def test_get_meta_safe():
    image = Image()

    assert image.get_meta_safe(int, 0) == 0

    image.meta[int] = 1
    assert image.get_meta_safe(int, 0) == 1
