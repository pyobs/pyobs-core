import io
import gzip
from astropy.io import fits
import numpy as np

from pytel.vfs import GzipReader, GzipWriter


def test_decompress():
    # test string
    test = b'Hello world'

    # create input stream
    with io.BytesIO(gzip.compress(test)) as bio:
        # create decompress stream
        with GzipReader(bio) as dr:
            # check
            assert dr.read() == test


def test_compress():
    # test string
    test = b'Hello world'

    # create output stream
    with io.BytesIO() as bio:
        # create compress stream
        with GzipWriter(bio, close_fd=False) as dr:
            # write data
            dr.write(test)

        # decompress and check
        assert gzip.decompress(bio.getvalue()) == test


def test_fits(tmpdir):
    # get test filename
    filename = tmpdir.join('test.fits')

    # create test fits file
    size = (42, 100)
    hdu = fits.PrimaryHDU(np.zeros(size))

    # write compressed file
    with open(str(filename), 'wb') as f:
        with GzipWriter(f) as gw:
            hdu.writeto(gw)

    # read compressed file
    with open(str(filename), 'rb') as f:
        with GzipReader(f) as gw:
            # read file
            hdus = fits.open(gw)

            # check
            assert hdus[0].data.shape == size

            # close
            hdus.close()
