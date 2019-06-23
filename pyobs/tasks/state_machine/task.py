import threading
from enum import Enum
from typing import Union
from pyobs.utils.time import Time
from pyobs.tasks.task import Task


class StateMachineTask(Task):
    """Base class for all tasks for the state machine."""

    class State(Enum):
        INIT = 'init'
        RUNNING = 'running'
        FINISHED = 'finished'

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

        # state
        self._state = StateMachineTask.State.INIT

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

    def __call__(self, closing_event: threading.Event, *args, **kwargs):
        """Run the task.

        Args:
            closing_event: Event to be set when task should close.
        """

        # which state?
        if self._state == StateMachineTask.State.INIT:
            # init task
            self._init(closing_event)
        elif self._state == StateMachineTask.State.RUNNING:
            # do step
            self._step(closing_event)
        else:
            # just sleep a little
            closing_event.wait(10)

    def _init(self, closing_event: threading.Event):
        """Init task.

        Args:
            closing_event: Event to be set when task should close.
        """
        pass

    def _step(self, closing_event: threading.Event):
        """Single step for a task.

        Args:
            closing_event: Event to be set when task should close.
        """
        pass

    def _finish(self):
        """Final steps for a task."""
        pass

    def finish(self):
        """Final steps for a task."""
        if self._state != StateMachineTask.State.FINISHED:
            self._finish()

    def get_fits_headers(self) -> dict:
        """Returns FITS header for the current status of the telescope.

        Returns:
            Dictionary containing FITS headers.
        """

        if self._exposure is not None:
            return {'EXP': (self._exposure, 'Number of exposure within observation')}
        else:
            return {}


__all__ = ['StateMachineTask']
