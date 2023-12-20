from collections import deque
from typing import Tuple, Optional, cast

from pyobs.images import Image
from pyobs.utils.enums import ImageType


class _CalibrationCache:
    BINNING_FORMAT = "{0}x{0}"

    def __init__(self, max_size: int):
        self._cache: deque[Tuple[Tuple[ImageType, str, str, Optional[str]], Image]] = deque([], max_size)

    def add_to_cache(self, image: Image, image_type: ImageType):
        cache_keys = self._get_cache_keys(image, image_type)
        cache_entry = (cache_keys, image)
        self._cache.append(cache_entry)

    def get_from_cache(self, image: Image, image_type: ImageType):
        cache_keys = self._get_cache_keys(image, image_type)
        return self._find_cache_entry(cache_keys)

    def _find_cache_entry(self, keys: Tuple[ImageType, str, str, Optional[str]]):
        for m, item in self._cache:
            if m == keys:
                return item

        raise ValueError("Calibration not found in cache.")

    def _get_cache_keys(self, image: Image, image_type: ImageType) -> Tuple[ImageType, str, str, Optional[str]]:
        instrument, binning, filter_name = self._get_image_cache_keys(image)
        cache_keys = (image_type, instrument, binning, filter_name)

        return cache_keys

    def _get_image_cache_keys(self, image: Image) -> Tuple[str, str, Optional[str]]:
        instrument = image.header["INSTRUME"]
        binning = self.BINNING_FORMAT.format(image.header["XBINNING"])

        filter_name = None
        if "FILTER" in image.header:
            filter_name = cast(str, image.header["FILTER"])

        return instrument, binning, filter_name
