import pytest

from pyobs.images import Image
from pyobs.utils.guiding_stat.guiding_stat_calculator import GuidingStatCalculator
from pyobs.images.meta import PixelOffsets, RaDecOffsets, AltAzOffsets
from pyobs.utils.guiding_stat.exposure_session_container import ExposureSessionContainer


@pytest.fixture()
def mock_meta_image():
    image = Image()
    image.set_meta(PixelOffsets(1.0, 1.0))
    image.set_meta(RaDecOffsets(2.0, 2.0))
    image.set_meta(AltAzOffsets(3.0, 3.0))
    return image


def test_init():
    gsc = GuidingStatCalculator(PixelOffsets)
    assert gsc._stat_meta_class == PixelOffsets
    assert isinstance(gsc._sessions, ExposureSessionContainer)


def test_pixel_offset(mock_meta_image):
    gsc = GuidingStatCalculator(PixelOffsets)
    gsc.init_stat("camera")
    gsc.add_data(mock_meta_image)
    data = gsc.get_stat("camera")

    assert data == (1.0, 1.0)

    with pytest.raises(KeyError):
        gsc.get_stat("camera")