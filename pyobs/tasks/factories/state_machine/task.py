from typing import Union
from pyobs.utils.time import Time
from ...task import Task


class StateMachineTask(Task):
    """Base class for all tasks for the state machine."""

    def __init__(self, start=None, end=None, *args, **kwargs):
        """Initializes a new Task.

        Args:
            start: Start time for task.
            end: End time for task.
        """
        Task.__init__(self, *args, **kwargs)

        # store start end end time
        self._start = self._parse_time(start)
        self._end = self._parse_time(end)

    def _parse_time(self, t: Union[Time, str]):
        """Parse a given time."""

        # if it's a Time already, just return it
        if isinstance(t, Time):
            return t

        # if it contains a whitespace or a "T", we assume that it contains a date
        if ' ' in t or 'T' in t:
            return Time(t)

        # otherwise, add current date
        return Time(Time.now().iso[:10] + ' ' + t)

    def __contains__(self, time: Time):
        """Whether the given time is in the interval of this task."""
        return self._start <= time < self._end

    def start(self):
        """Initial steps for a task."""
        pass

    def stop(self):
        """Final steps for a task."""
        pass


__all__ = ['StateMachineTask']
