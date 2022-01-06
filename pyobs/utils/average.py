import datetime
from typing import List, Optional, Tuple

import numpy as np


class RollingTimeAverage(object):
    def __init__(self, interval: float):
        self._interval = interval
        self._values: List[Tuple[datetime.datetime, float]] = []
        self._start_time = datetime.datetime.utcnow()

    def clear(self) -> None:
        self._values = []
        self._start_time = datetime.datetime.utcnow()

    def add(self, value: float) -> None:
        # add value
        now = datetime.datetime.utcnow()
        self._values.append((now, value))

        # clean up
        self._values = [(time, value) for time, value in self._values if (now - time).total_seconds() < self._interval]

    def average(self, min_interval: Optional[float] = None) -> Optional[float]:
        # got values?
        if len(self._values) == 0:
            return None

        # get time
        now = datetime.datetime.utcnow()

        # go no values older than now-interval?
        if min_interval:
            values = [value for time, value in self._values if (now - time).total_seconds() > min_interval]
            if len(values) == 0:
                return None

        # get values and average
        values = [value for time, value in self._values if (now - time).total_seconds() < self._interval]
        return float(np.mean(values))


__all__ = ["RollingTimeAverage"]
