from astropy.io import fits
import pytest

from astroplan import Observer
import astropy.units as u
from pyobs.utils.fits import format_filename


@pytest.fixture
def observer():
    return Observer(timezone='utc', longitude=20.810808 * u.deg, latitude=-32.375823 * u.deg, elevation=1798. * u.m)


def test_default(observer):
    hdr = fits.Header()

    # convert, should throw a KeyError
    with pytest.raises(KeyError):
        format_filename(hdr, 'image_{FILTER}.fits', observer)

    # add filter
    hdr['FILTER'] = 'clear'
    filename = format_filename(hdr, 'image_{FILTER}.fits', observer)
    assert 'image_clear.fits' == filename


def test_date_obs(observer):
    hdr = fits.Header({'DATE-OBS': '2019-03-26T19:46:23.000'})

    assert '2019-03-26T19:46:23.000' == format_filename(hdr, '{DATE-OBS}', observer)
    assert '19-46-23' == format_filename(hdr, '{DATE-OBS|time}', observer)
    assert '2019-03-26' == format_filename(hdr, '{DATE-OBS|date}', observer)
    assert '20190326' == format_filename(hdr, '{DATE-OBS|night}', observer)


def test_filter(observer):
    hdr = fits.Header({'IMAGETYP': 'light', 'FILTER': 'clear'})

    # for dark/bias no filter should be added
    hdr['IMAGETYP'] = 'dark'
    hdr['FILTER'] = 'clear'
    assert 'image_dark.fits' == format_filename(hdr, 'image_{IMAGETYP}{FILTER|filter}.fits', observer)

    # for light it should
    hdr['IMAGETYP'] = 'light'
    assert 'image_light_clear.fits' == format_filename(hdr, 'image_{IMAGETYP}{FILTER|filter}.fits', observer)


def test_string(observer):
    hdr = fits.Header({'EXPID': 5})

    # format number
    assert 'exp5' == format_filename(hdr, 'exp{EXPID|string:d}', observer)
    assert 'exp0005' == format_filename(hdr, 'exp{EXPID|string:04d}', observer)


def test_list(observer):
    hdr = fits.Header({'EXPID': 5})

    # list of formats
    fmt = ['exp{EXPBLA|sring:d}', 'exp{EXPID|string:d}']

    # format number
    assert 'exp5' == format_filename(hdr, fmt, observer)

    # list of formats
    fmt = ['exp', 'exp{EXPID|string:d}']

    # format number
    assert 'exp' == format_filename(hdr, fmt, observer)
