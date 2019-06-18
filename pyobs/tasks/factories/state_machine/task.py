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
        self._start = Time(start) if isinstance(start, str) else start
        self._end = Time(end) if isinstance(end, str) else end

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
