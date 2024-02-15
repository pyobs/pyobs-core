import itertools
from typing import List, Any

import numpy as np
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
        boxes = photutils.psf.extract_stars(
            NDData(image.data.astype(float)), sources, size=self._box_size
        ).all_stars

        self._check_overlapping_boxes(boxes)
        return boxes

    def _check_sources_count(self, sources: Table) -> None:
        if len(sources) < self._min_sources:
            raise ValueError(f"Only {len(sources)} source(s) in image, but at least {self._min_sources} required.")

    def _check_overlapping_boxes(self, boxes: List[EPSFStar]) -> None:
        for (box_1, box_2) in itertools.combinations(boxes, 2):
            self._check_overlapping_box_pair(box_1.center, box_2.center)

    def _check_overlapping_box_pair(self, box_center_1: np.ndarray[Any, Any], box_center_2: np.ndarray[Any, Any]) -> None:
        dist_2d = np.abs(np.subtract(box_center_1, box_center_2))

        if dist_2d[0] < self._box_size / 2 or dist_2d[1] < self._box_size / 2:
            raise ValueError("Boxes are overlapping!")
