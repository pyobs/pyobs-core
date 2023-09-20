import pytest

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, SkyOffsets
from pyobs.modules.pointing._baseguiding import _GuidingStatistics


@pytest.fixture()
def mock_meta_image():
    image = Image()
    image.set_meta(PixelOffsets(1.0, 1.0))
    return image


def test_pixel_offset(mock_meta_image):
    gsc = _GuidingStatistics()
    gsc.reset_stats("camera")
    gsc.add_data(mock_meta_image)
    gsc.add_data(mock_meta_image)
    data = gsc.get_stats("camera")

    assert data == (1.0, 1.0)

    with pytest.raises(KeyError):
        gsc.get_stats("camera")


def test_calc_rms():
    gsc = _GuidingStatistics()
    assert gsc._calc_rms([]) == ()
    assert gsc._calc_rms([(1.0, 1.0), (1.0, 7.0)]) == (1.0, 5.0)


def test_missing_meta():
    gsc = _GuidingStatistics()
    gsc.reset_stats("camera")
    img = Image()

    with pytest.raises(KeyError):
        gsc.add_data(img)
