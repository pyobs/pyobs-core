import logging
from typing import List, Tuple

import numpy as np

from pyobs.images import Image
from pyobs.object import get_class_from_string
from pyobs.utils.guiding_stat.exposure_session_container import ExposureSessionContainer

log = logging.getLogger(__name__)


class GuidingStatCalculator:
    def __init__(self, stat_meta_class: str):
        self._stat_meta_class = get_class_from_string(stat_meta_class)
        self._sessions = ExposureSessionContainer()

    def init_stat(self, client: str) -> None:
        """
        Initializes a stat measurement session for a client
        Args:
            client: name/id of the client
        """
        self._sessions.init_session(client)

    def _calc_rms(self, data: List[Tuple[float, float]]) -> tuple:
        if len(data) == 0:
            return ()

        flattened_data = np.array(list(map(list, zip(*data))))
        data_len = len(flattened_data[0])
        rms = np.sqrt(np.sum(np.power(flattened_data, 2), axis=1) / data_len)
        return tuple(rms)

    def get_stat(self, client: str) -> Tuple[float, float]:
        """
        Retrieves the RMS of the measured stat for a client session.
        The client session is ended on retrieval.
        Args:
            client: id/name of the client

        Returns:
            RMS of the measured stat
        """
        data = self._sessions.pop_session(client)
        return self._calc_rms(data)

    def add_data(self, image: Image) -> None:
        """
        Adds metadata from an image to all client measurement sessions.
        Args:
            image: Image witch metadata
        """

        if not image.has_meta(self._stat_meta_class):
            log.warning("Image is missing the necessary meta information!")
            return

        data = tuple(image.get_meta(self._stat_meta_class).__dict__.values())

        self._sessions.add_data_to_all(data)
