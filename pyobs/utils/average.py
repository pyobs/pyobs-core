import datetime
import numpy as np


class RollingTimeAverage(object):
    def __init__(self, interval):
        self._interval = interval
        self._values = []
        self._start_time = datetime.datetime.utcnow()

    def clear(self):
        self._values = []
        self._start_time = datetime.datetime.utcnow()

    def add(self, value):
        # add value
        now = datetime.datetime.utcnow()
        self._values.append((now, value))

        # clean up
        self._values = [(time, value) for time, value in self._values if (now-time).total_seconds() < self._interval]

    def average(self, min_interval: float = None):
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
        return np.mean(values)


__all__ = ['RollingTimeAverage']
