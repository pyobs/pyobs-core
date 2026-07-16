import numpy as np
import pytest
from astropy.io import fits

from pyobs.utils.fits import fitssec, parse_section_bounds


class DummyHdu:
    def __init__(self, data, header):
        self.data = data
        self.header = header


def test_parse_section_bounds_absent():
    assert parse_section_bounds(fits.Header(), "TRIMSEC") is None


def test_parse_section_bounds_valid():
    header = fits.Header()
    header["TRIMSEC"] = "[2:4,3:5]"

    assert parse_section_bounds(header, "TRIMSEC") == (1, 4, 2, 5)


def test_parse_section_bounds_invalid():
    header = fits.Header()
    header["TRIMSEC"] = "INVALID"

    with pytest.raises(ValueError):
        parse_section_bounds(header, "TRIMSEC")


def test_fitssec_no_keyword():
    data = np.arange(16).reshape(4, 4)
    hdu = DummyHdu(data, fits.Header())

    np.testing.assert_array_equal(fitssec(hdu), data)


def test_fitssec_with_keyword():
    data = np.arange(16).reshape(4, 4)
    header = fits.Header()
    header["TRIMSEC"] = "[2:4,2:4]"
    hdu = DummyHdu(data, header)

    np.testing.assert_array_equal(fitssec(hdu), data[1:4, 1:4])
