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

    """
    hdr = fits.Header({'DATE-OBS': '2019-03-26T19:46:23.000'})
    filename = format_filename(hdr, '{DATE-OBS}', env)
    print(filename)
    filename = format_filename(hdr, '{DATE-OBS|time}', env)
    print(filename)
    filename = format_filename(hdr, '{DATE-OBS|time:-}', env)
    print(filename)
    filename = format_filename(hdr, '{DATE-OBS|date:-}', env)
    print(filename)
    filename = format_filename(hdr, '{DATE-OBS|night}', env)
    print(filename)

    hdr['IMAGETYP'] = 'dark'
    hdr['FILTER'] = 'clear'
    fmt = '/cache/pyobs_{DATE-OBS|date}T{DATE-OBS|time:-}_{IMAGETYP}{FILTER|filter}.fits.gz'
    filename = format_filename(hdr, fmt, env)
    print(filename)
    """
