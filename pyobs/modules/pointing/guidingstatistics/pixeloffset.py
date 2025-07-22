import logging
from typing import Any
import numpy as np

from pyobs.images import Image
from .guidingstatistics import GuidingStatistics
from pyobs.images.meta import PixelOffsets


log = logging.getLogger(__name__)


class GuidingStatisticsPixelOffset(GuidingStatistics[Image, tuple[float, float]]):
    @staticmethod
    def _calc_rms(data: list[tuple[float, float]]) -> tuple[float, float] | None:
        """
        Calculates RMS of data.

        Args:
            data: Data to calculate RMS for.

        Returns:
            Tuple of RMS.
        """
        if len(data) < 3:
            return None

        flattened_data = np.array(list(map(list, zip(*data))))
        data_len = len(flattened_data[0])
        rms = np.sqrt(np.sum(np.power(flattened_data, 2), axis=1) / data_len)
        return tuple(rms)

    def _build_header(self, data: list[tuple[float, float]]) -> dict[str, tuple[Any, str]]:
        header = {}
        rms = self._calc_rms(data)

        if rms is not None:
            header["GUIDING RMS1"] = (float(rms[0]), "RMS for guiding on axis 1")
            header["GUIDING RMS2"] = (float(rms[1]), "RMS for guiding on axis 2")

        return header

    def _get_session_data(self, data: Image) -> tuple[float, float]:
        if data.has_meta(PixelOffsets):
            meta = data.get_meta(PixelOffsets)
            primitive = tuple(meta.__dict__.values())
            return primitive
        else:
            log.warning("Image is missing the necessary meta information!")
            raise KeyError("Unknown meta.")
