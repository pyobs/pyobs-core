from astropy.io import fits
import pytest

from pyobs import Environment
from pyobs.utils.fits import format_filename


@pytest.fixture
def env():
    return Environment(timezone='utc',
                       location={'longitude': 20.810808, 'latitude': -32.375823, 'elevation': 1798.})


def test_default(env):
    hdr = fits.Header()

    # convert, should throw a KeyError
    with pytest.raises(KeyError):
        format_filename(hdr, 'image_{FILTER}.fits', env)

    # add filter
    hdr['FILTER'] = 'clear'
    filename = format_filename(hdr, 'image_{FILTER}.fits', env)
    assert 'image_clear.fits' == filename


def test_date_obs(env):
    hdr = fits.Header({'DATE-OBS': '2019-03-26T19:46:23.000'})

    assert '2019-03-26T19:46:23.000' == format_filename(hdr, '{DATE-OBS}', env)
    assert '19:46:23' == format_filename(hdr, '{DATE-OBS|time}', env)
    assert '19-46-23' == format_filename(hdr, '{DATE-OBS|time:-}', env)
    assert '2019-03-26' == format_filename(hdr, '{DATE-OBS|date}', env)
    assert '20190326' == format_filename(hdr, '{DATE-OBS|night}', env)


def test_filter(env):
    hdr = fits.Header({'IMAGETYP': 'light', 'FILTER': 'clear'})

    # for dark/bias no filter should be added
    hdr['IMAGETYP'] = 'dark'
    hdr['FILTER'] = 'clear'
    assert 'image_dark.fits' == format_filename(hdr, 'image_{IMAGETYP}{FILTER|filter}.fits', env)

    # for light it should
    hdr['IMAGETYP'] = 'light'
    assert 'image_light_clear.fits' == format_filename(hdr, 'image_{IMAGETYP}{FILTER|filter}.fits', env)


def test_string(env):
    hdr = fits.Header({'EXPID': 5})

    # format number
    assert 'exp5' == format_filename(hdr, 'exp{EXPID|string:d}', env)
    assert 'exp0005' == format_filename(hdr, 'exp{EXPID|string:04d}', env)
