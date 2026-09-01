from __future__ import annotations

from collections import deque
from typing import cast

from pyobs.images import Image
from pyobs.utils.enums import ImageType


class _CalibrationCache:
    BINNING_FORMAT = "{0}x{0}"

    def __init__(self, max_size: int):
        self._cache: deque[tuple[tuple[ImageType, str, str, str | None, float | None], Image]] = deque([], max_size)

    def add_to_cache(self, image: Image, image_type: ImageType, exptime: float | None = None) -> None:
        cache_keys = self._get_cache_keys(image, image_type, exptime)
        cache_entry = (cache_keys, image)
        self._cache.append(cache_entry)

    def get_from_cache(self, image: Image, image_type: ImageType, exptime: float | None = None) -> Image:
        cache_keys = self._get_cache_keys(image, image_type, exptime)
        return self._find_cache_entry(cache_keys)

    def _find_cache_entry(self, keys: tuple[ImageType, str, str, str | None, float | None]) -> Image:
        for m, item in self._cache:
            if m == keys:
                return item

        raise ValueError("Calibration not found in cache.")

    def _get_cache_keys(
        self, image: Image, image_type: ImageType, exptime: float | None = None
    ) -> tuple[ImageType, str, str, str | None, float | None]:
        instrument, binning, filter_name = self._get_image_cache_keys(image)
        if image_type in (ImageType.BIAS, ImageType.DARK):
            # BIAS/DARK lookups ignore filter (matching Calibration._find_master_in_archive,
            # which never passes a science image's FILTER to Pipeline.find_master for these two
            # types). Deriving filter_name from whichever image was passed -- the science image
            # on a get, the master on an add -- would otherwise near-guarantee a cache miss:
            # a master dark/bias frequently has no FILTER header at all (or a stale one from
            # whatever was mounted at the time) while the science image usually does.
            filter_name = None
        # exptime is not derived from `image`'s own header: for DARK, callers pass the exptime
        # they searched for (the science exptime for an exact match, or the configured
        # reference exptime for a scale-down lookup), which generally differs from either the
        # science image's or the master's own EXPTIME. None for BIAS/SKYFLAT, unchanged.
        cache_keys = (image_type, instrument, binning, filter_name, exptime)

        return cache_keys

    def _get_image_cache_keys(self, image: Image) -> tuple[str, str, str | None]:
        instrument = image.header["INSTRUME"]
        binning = self.BINNING_FORMAT.format(image.header["XBINNING"])  # noqa: UP031

        filter_name = None
        if "FILTER" in image.header:
            filter_name = cast(str, image.header["FILTER"])

        return instrument, binning, filter_name
