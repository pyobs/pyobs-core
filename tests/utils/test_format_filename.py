from astropy.io import fits
import pytest

import astropy.units as u
from pyobs.utils.fits import format_filename


def test_default():
    hdr = fits.Header()

    # convert, should throw a KeyError
    with pytest.raises(KeyError):
        format_filename(hdr, "image_{FILTER}.fits")

    # add filter
    hdr["FILTER"] = "clear"
    filename = format_filename(hdr, "image_{FILTER}.fits")
    assert "image_clear.fits" == filename


def test_date_obs():
    hdr = fits.Header({"DATE-OBS": "2019-03-26T19:46:23.000"})

    assert "2019-03-26T19:46:23.000" == format_filename(hdr, "{DATE-OBS}")
    assert "19-46-23" == format_filename(hdr, "{DATE-OBS|time:-}")
    assert "2019-03-26" == format_filename(hdr, "{DATE-OBS|date:-}")


def test_filter():
    hdr = fits.Header({"IMAGETYP": "light", "FILTER": "clear"})

    # for dark/bias no filter should be added
    hdr["IMAGETYP"] = "dark"
    hdr["FILTER"] = "clear"
    assert "image_dark.fits" == format_filename(hdr, "image_{IMAGETYP}{FILTER|filter}.fits")

    # for light it should
    hdr["IMAGETYP"] = "light"
    assert "image_light-clear.fits" == format_filename(hdr, "image_{IMAGETYP}{FILTER|filter}.fits")


def test_string():
    hdr = fits.Header({"EXPID": 5})

    # format number
    assert "exp5" == format_filename(hdr, "exp{EXPID|string:d}")
    assert "exp0005" == format_filename(hdr, "exp{EXPID|string:04d}")


def test_list():
    hdr = fits.Header({"EXPID": 5})

    # list of formats
    fmt = ["exp{EXPBLA|sring:d}", "exp{EXPID|string:d}"]

    # format number
    assert "exp5" == format_filename(hdr, fmt)

    # list of formats
    fmt = ["exp", "exp{EXPID|string:d}"]

    # format number
    assert "exp" == format_filename(hdr, fmt)
