import numpy as np
import pytest
from astropy.coordinates import SkyCoord

from pyobs.images import Image
from pyobs.images.meta import SkyOffsets
from pyobs.modules.pointing.guidingstatistics import GuidingStatisticsSkyOffset


@pytest.fixture()
def mock_meta_image() -> Image:
    image = Image()

    coord0 = SkyCoord(alt=90.0, az=0.0, unit="degree", frame="altaz")
    coord1 = SkyCoord(alt=80.0, az=0.0, unit="degree", frame="altaz")

    image.set_meta(SkyOffsets(coord0, coord1))
    return image


def test_end_to_end(mock_meta_image) -> None:
    client = "camera"
    statistic = GuidingStatisticsSkyOffset()

    statistic.init_stats(client)

    statistic.add_data(mock_meta_image)
    statistic.add_data(mock_meta_image)
    statistic.add_data(mock_meta_image)

    header = statistic.add_to_header(client, {})

    np.testing.assert_almost_equal(header["GUIDING RMS"][0], 10.0)
    assert header["GUIDING RMS"][1] == "RMS for guiding on sky"


def test_build_header_to_few_values() -> None:
    guiding_stat = GuidingStatisticsSkyOffset()
    assert guiding_stat._build_header([1.0]) == {}


def test_get_session_data() -> None:
    image = Image()
    guiding_stat = GuidingStatisticsSkyOffset()

    assert guiding_stat._get_session_data(image) is None
