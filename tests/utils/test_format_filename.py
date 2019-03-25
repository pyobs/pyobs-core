from astropy.io import fits
import pytest

from pyobs import Environment
from pyobs.utils.fits import format_filename


@pytest.fixture
def env():
    return Environment(timezone='utc',
                       location={'longitude': 20.810808, 'latitude': -32.375823, 'elevation': 1798.})


def test_default(env):
    # test format and hdu
    fmt = '/cache/pyobs_{date}T{time}{type}.fits.gz'
    hdr = fits.Header()

    # convert, should throw a KeyError
    with pytest.raises(KeyError):
        filename = format_filename(hdr, fmt, env, 'test.fits')

    # add date-obs and convert
    hdr['DATE-OBS'] = '2019-03-26T19:46:23.000'
    with pytest.raises(KeyError):
        filename = format_filename(hdr, fmt, env, 'test.fits')

    # add image type and convert
    hdr['IMAGETYP'] = 'DARK'
    filename = format_filename(hdr, fmt, env, 'test.fits')
    assert '/cache/pyobs_2019-03-26T19-46-23_DARK.fits.gz' == filename


def test_fits_headers(env):
    # test header
    hdr = fits.Header({'TELESCOP': 'monet'})

    # case must match
    with pytest.raises(KeyError):
        format_filename(hdr, '{telescop}_test.fits', env, 'test.fits')

    # this should work
    filename = format_filename(hdr, '{TELESCOP}_test.fits', env, 'test.fits')
    assert 'monet_test.fits' == filename
