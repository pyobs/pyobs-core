from typing import List, Tuple

import numpy as np

from pyobs.images import Image
from pyobs.utils.guiding_stat.exposure_session_container import ExposureSessionContainer


class GuidingStatCalculator:
    def __init__(self, stat_meta_class: type[object]):
        self._stat_meta_class = stat_meta_class
        self._sessions = ExposureSessionContainer()

    def init_stat(self, client: str) -> None:
        self._sessions.init_session(client)

    def _calc_rms(self, data: List[Tuple[float, float]]) -> tuple:
        if len(data) == 0:
            return ()

        flattened_data = np.array(list(map(list, zip(*data))))
        data_len = len(flattened_data[0])
        rms = np.sqrt(np.sum(np.power(flattened_data, 2), axis=1)/data_len)
        return tuple(rms)

    def get_stat(self, client: str) -> Tuple[float, float]:
        data = self._sessions.pop_session(client)
        return self._calc_rms(data)

    def add_data(self, image: Image):
        if not image.has_meta(self._stat_meta_class):
            raise KeyError("Image has not the necessary meta information!")

        data = tuple(image.get_meta(self._stat_meta_class).__dict__.values())

        self._sessions.add_data_to_all(data)