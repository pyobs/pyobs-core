import pytest

from pyobs.images import Image
from pyobs.images.meta import PixelOffsets, SkyOffsets
from pyobs.modules.pointing.guidingstatistics import GuidingStatisticsPixelOffset


@pytest.fixture()
def mock_meta_image() -> Image:
    image = Image()
    image.set_meta(PixelOffsets(1.0, 1.0))
    return image


def test_end_to_end(mock_meta_image) -> None:
    client = "camera"
    statistic = GuidingStatisticsPixelOffset()

    statistic.init_stats(client)

    statistic.add_data(mock_meta_image)
    statistic.add_data(mock_meta_image)
    statistic.add_data(mock_meta_image)

    header = statistic.add_to_header(client, {})

    assert header["GUIDING RMS1"] == (1.0, "RMS for guiding on axis 1")
    assert header["GUIDING RMS2"] == (1.0, "RMS for guiding on axis 2")


def test_build_header_to_few_values() -> None:
    gspo = GuidingStatisticsPixelOffset()
    assert gspo._build_header([(1.0, 1.0)]) == {}


def test_get_session_data() -> None:
    image = Image()
    gspo = GuidingStatisticsPixelOffset()

    with pytest.raises(KeyError):
        gspo._get_session_data(image)
