import pytest

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, SkyOffsets
from pyobs.utils.guiding_stat.exposure_session_container import ExposureSessionContainer
from pyobs.utils.guiding_stat.guiding_stat_calculator import GuidingStatCalculator


@pytest.fixture()
def mock_meta_image():
    image = Image()
    image.set_meta(PixelOffsets(1.0, 1.0))
    return image


def test_init():
    gsc = GuidingStatCalculator(PixelOffsets)
    assert gsc._stat_meta_class == PixelOffsets
    assert isinstance(gsc._sessions, ExposureSessionContainer)


def test_pixel_offset(mock_meta_image):
    gsc = GuidingStatCalculator(PixelOffsets)
    gsc.init_stat("camera")
    gsc.add_data(mock_meta_image)
    gsc.add_data(mock_meta_image)
    data = gsc.get_stat("camera")

    assert data == (1.0, 1.0)

    with pytest.raises(KeyError):
        gsc.get_stat("camera")


def test_calc_rms():
    gsc = GuidingStatCalculator(PixelOffsets)
    assert gsc._calc_rms([]) == ()
    assert gsc._calc_rms([(1.0, 1.0), (1.0, 7.0)]) == (1.0, 5.0)


def test_missing_meta(mock_meta_image):
    gsc = GuidingStatCalculator(SkyOffsets)
    gsc.init_stat("camera")

    with pytest.raises(KeyError):
        gsc.add_data(mock_meta_image)
