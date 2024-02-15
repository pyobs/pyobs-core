from typing import List

import photutils
from astropy.nddata import NDData
from astropy.table import Table
from photutils.psf import EPSFStar

from pyobs.images import Image


class _BoxGenerator(object):
    def __init__(self, max_offset: float, min_sources: int) -> None:
        self._box_size = self._max_offset_to_box_size(max_offset)
        self._min_sources = min_sources

    @staticmethod
    def _max_offset_to_box_size(max_offset: float) -> int:
        box_size = 2 * max_offset + 1   # photutils.psf.extract_stars only accepts uneven box sizes
        return int(box_size)

    def __call__(self, image: Image) -> List[EPSFStar]:
        sources = image.catalog
        self._check_sources_count(sources)

        # extract boxes
        return photutils.psf.extract_stars(
            NDData(image.data.astype(float)), sources, size=self._box_size
        ).all_stars

    def _check_sources_count(self, sources: Table) -> None:
        """Check if enough sources in table.

        Args:
            sources: table of sources.

        Returns:
            None

        Raises:
            ValueError if not at least self.min_sources in sources table

        """

        if len(sources) < self._min_sources:
            raise ValueError(f"Only {len(sources)} source(s) in image, but at least {self._min_sources} required.")
