import logging
from typing import List, Dict, Tuple, Any, Optional

import numpy as np

from pyobs.images import Image
from pyobs.images.meta import SkyOffsets
from .guidingstatistics import GuidingStatistics

log = logging.getLogger(__name__)


class GuidingStatisticsSkyOffset(GuidingStatistics[Image, float]):
    @staticmethod
    def _calc_rms(data: List[float]) -> Optional[float]:
        """
        Calculates RMS of data.

        Args:
            data: Data to calculate RMS for.

        Returns:
            Tuple of RMS.
        """
        if len(data) < 3:
            return None

        data_len = len(data)
        rms = np.sqrt(np.sum(np.power(data, 2)) / data_len)
        return float(rms)

    def _build_header(self, data: List[float]) -> Dict[str, Tuple[Any, str]]:
        header = {}
        rms = self._calc_rms(data)

        if rms is not None:
            header["GUIDING RMS"] = (float(rms), "RMS for guiding on sky")

        return header

    def _get_session_data(self, data: Image) -> float | None:
        if data.has_meta(SkyOffsets):
            sky_offset = data.get_meta(SkyOffsets)
            return float(sky_offset.separation().deg)
        else:
            return None
