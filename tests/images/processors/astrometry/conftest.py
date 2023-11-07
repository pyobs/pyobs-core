import pytest
from astropy.io.fits import Header


@pytest.fixture(scope="module")
def mock_header():
    header = Header()
    header["CDELT1"] = 1.0
    header["CDELT2"] = 1.0

    header["TEL-RA"] = 0.0
    header["TEL-DEC"] = 0.0

    header["NAXIS1"] = 1.0
    header["NAXIS2"] = 1.0

    header["CRPIX1"] = 1.0
    header["CRPIX2"] = 1.0

    for keyword in ["PC1_1", "PC1_2", "PC2_1", "PC2_2"]:
        header[keyword] = 0.0

    return header