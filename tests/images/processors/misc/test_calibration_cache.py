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
    cached_image.header["INSTRUME"] = "cam"
    cached_image.header["XBINNING"] = 1
    cached_image.header["FILTER"] = "filter"
    image_type = ImageType.OBJECT

    cache = _CalibrationCache(5)
    cache.add_to_cache(cached_image, image_type)

    result_image = cache.get_from_cache(mock_image, image_type)

    assert cached_image == result_image


def test_add_to_cache(mock_image):
    image_type = ImageType.OBJECT

    cache = _CalibrationCache(5)
    cache.add_to_cache(mock_image, image_type)

    assert cache.get_from_cache(mock_image, image_type) == mock_image


def test_add_to_cache_size(mock_image):
    other_image = Image()
    other_image.header["INSTRUME"] = "cam"
    other_image.header["XBINNING"] = 1
    other_image.header["FILTER"] = "filter"
    image_type = ImageType.OBJECT

    cache = _CalibrationCache(1)
    cache.add_to_cache(other_image, image_type)
    cache.add_to_cache(mock_image, image_type)

    # maxlen=1, so the old entry must have been evicted -- only the new one is retrievable
    assert cache.get_from_cache(mock_image, image_type) == mock_image


def test_find_cache_entry_emtpy():
    image_type = ImageType.OBJECT
    image_instrument = "cam"
    image_binning = "1x1"
    image_filter = "filter"
    cache = _CalibrationCache(2)

    with pytest.raises(ValueError):
        cache._find_cache_entry((image_type, image_instrument, image_binning, image_filter, None))


# ── exptime keying (DARK masters at different exptimes) ─────────────────────


@pytest.fixture()
def dark_lookup_image():
    # instrument/binning matching _dark_master()'s, no FILTER -- DARK lookups ignore filter, and
    # a real dark master's own FITS header often doesn't carry one either (see _get_cache_keys)
    image = Image()
    image.header["INSTRUME"] = "cam"
    image.header["XBINNING"] = 1
    return image


def _dark_master() -> Image:
    master = Image()
    master.header["INSTRUME"] = "cam"
    master.header["XBINNING"] = 1
    return master


def test_get_from_cache_keys_by_exptime(dark_lookup_image):
    exact = _dark_master()
    reference = _dark_master()

    cache = _CalibrationCache(5)
    cache.add_to_cache(exact, ImageType.DARK, exptime=45.0)
    cache.add_to_cache(reference, ImageType.DARK, exptime=600.0)

    assert cache.get_from_cache(dark_lookup_image, ImageType.DARK, exptime=45.0) == exact
    assert cache.get_from_cache(dark_lookup_image, ImageType.DARK, exptime=600.0) == reference


def test_get_from_cache_miss_for_different_exptime(dark_lookup_image):
    cache = _CalibrationCache(5)
    cache.add_to_cache(_dark_master(), ImageType.DARK, exptime=45.0)

    with pytest.raises(ValueError):
        cache.get_from_cache(dark_lookup_image, ImageType.DARK, exptime=600.0)


def test_exptime_defaults_to_none_unaffected_by_dark_entries(dark_lookup_image):
    # a BIAS/SKYFLAT lookup (exptime=None, the default) must not collide with a DARK entry
    # cached under an explicit exptime
    cache = _CalibrationCache(5)
    cache.add_to_cache(_dark_master(), ImageType.DARK, exptime=600.0)

    with pytest.raises(ValueError):
        cache.get_from_cache(dark_lookup_image, ImageType.DARK)
