from pyobs.images.processors.photometry import SepPhotometry
from pyobs.images.processors.photometry._sep_aperture_photometry import _SepAperturePhotometry


def test_init():
    photometry = SepPhotometry()
    assert isinstance(photometry._calculator, _SepAperturePhotometry)
