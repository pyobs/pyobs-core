from pyobs.images.processors.photometry import PhotUtilsPhotometry
from pyobs.images.processors.photometry._photutil_aperture_photometry import _PhotUtilAperturePhotometry


def test_init():
    photometry = PhotUtilsPhotometry()
    assert isinstance(photometry._calculator, _PhotUtilAperturePhotometry)
