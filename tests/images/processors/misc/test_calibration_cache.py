from collections import deque

import pytest

from pyobs.images import Image
from pyobs.images.processors.calibration._calibration_cache import _CalibrationCache
from pyobs.utils.enums import ImageType


@pytest.fixture()
def mock_image():
    image = Image()
    image.header["INSTRUME"] = "cam"
    image.header["XBINNING"] = 1
    image.header["FILTER"] = "filter"
    image.header["DATE-OBS"] = "2023-11-20 07:53:29.653"

    return image


def test_get_from_cache(mock_image):
    cached_image = Image()
    image_type = ImageType.OBJECT
    image_instrument = "cam"
    image_binning = "1x1"
    image_filter = "filter"

    cache = _CalibrationCache(5)
    cache._cache = deque([((image_type, image_instrument, image_binning, image_filter), cached_image)], 5)

    result_image = cache.get_from_cache(mock_image, image_type)

    assert cached_image == result_image


def test_add_to_cache(mock_image):
    image_type = ImageType.OBJECT
    image_instrument = "cam"
    image_binning = "1x1"
    image_filter = "filter"

    cache = _CalibrationCache(5)
    cache.add_to_cache(mock_image, image_type)

    assert cache._cache[0] == ((image_type, image_instrument, image_binning, image_filter), mock_image)


def test_add_to_cache_size(mock_image):
    other_image = Image()
    image_type = ImageType.OBJECT
    image_instrument = "cam"
    image_binning = "1x1"
    image_filter = "filter"

    cache = _CalibrationCache(1)
    cache._cache = deque([((image_type, image_instrument, image_binning, image_filter), other_image)], 1)
    cache.add_to_cache(mock_image, image_type)

    assert cache._cache[0] == ((image_type, image_instrument, image_binning, image_filter), mock_image)


def test_find_cache_entry_emtpy():
    image_type = ImageType.OBJECT
    image_instrument = "cam"
    image_binning = "1x1"
    image_filter = "filter"
    cache = _CalibrationCache(2)

    with pytest.raises(ValueError):
        cache._find_cache_entry((image_type, image_instrument, image_binning, image_filter))
