import threading
from enum import Enum
from typing import Union
import astropy.units as u
from astropy.time import TimeDelta

from pyobs.utils.time import Time
from pyobs.tasks.task import Task


class StateMachineTask(Task):
    """Base class for all tasks for the state machine."""

    def __init__(self, *args, start=None, end=None, **kwargs):
        """Initializes a new Task.

        Args:
            start: Start time for task.
            end: End time for task.
        """
        Task.__init__(self, *args, **kwargs)

        # store start end end time
        self._start = self._parse_time(start)
        self._end = self._parse_time(end)

        # exposure number
        self._exposure = 0

    def _parse_time(self, t: Union[Time, str]):
        """Parse a given time."""

        # if it's a Time already, just return it
        if isinstance(t, Time):
            return t

        # if it starts with "sunrise" or "sunset", do some calculations
        if t.startswith('sunrise') or t.startswith('sunset'):
            # calculate next sunrise/sunset
            now = Time.now()
            time = self.observer.sun_rise_time(now) if t.startswith('sunrise') else self.observer.sun_set_time(now)

            # add or substract secons?
            if '+' in t:
                time += TimeDelta(float(t[t.index('+') + 1:]) * u.second)
            if '-' in t:
                time -= TimeDelta(float(t[t.index('-') + 1:]) * u.second)

            # finished
            return time

        # if it contains a whitespace or a "T", we assume that it contains a date
        if ' ' in t or 'T' in t:
            return Time(t)

        # otherwise, add current date
        return Time(Time.now().iso[:10] + ' ' + t)

    def is_observable(self, time: Time) -> bool:
        """Whether this task is observable at the given time.

        Args:
            time: Time to check.

        Returns:
            Observable or not.
        """

        # check time and state
        return Task.is_observable(self, time) and self._start <= time < self._end

    def get_fits_headers(self) -> dict:
        """Returns FITS header for the current status of the telescope.

        Returns:
            Dictionary containing FITS headers.
        """

        if self._exposure is not None:
            return {'EXP': (self._exposure, 'Number of exposure within observation')}
        else:
            return {}

    def finish(self):
        """Final steps for a task."""
        pass


__all__ = ['StateMachineTask']
