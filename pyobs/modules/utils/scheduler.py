import logging
import threading

import typing

from pyobs.interfaces import IStoppable

from pyobs import PyObsModule, get_object
from pyobs.robotic import BaseScheduler


log = logging.getLogger(__name__)


class Scheduler(PyObsModule, IStoppable):
    """Scheduler."""

    def __init__(self, scheduler: typing.Union[dict, BaseScheduler], interval: int = 300, *args, **kwargs):
        """Initialize a new scheduler.

        Args:
            scheduler: Scheduler to use
            interval: Interval between scheduler updates
        """
        PyObsModule.__init__(self, *args, **kwargs)

        # get scheduler
        self._scheduler = get_object(scheduler, BaseScheduler)

        # store
        self._interval = interval
        self._running = True

        # update thread
        self._abort_event = threading.Event()
        self._interval_event = threading.Event()
        self._add_thread_func(self._update_thread, True)

    def open(self):
        """Open module"""
        PyObsModule.open(self)

    def close(self):
        """Close module"""
        PyObsModule.close(self)

        # trigger events
        self._abort_event.set()
        self._interval_event.set()

    def start(self, *args, **kwargs):
        """Start scheduler."""
        self._running = True

    def stop(self, *args, **kwargs):
        """Stop scheduler."""
        self._running = False

        # reset event
        self._interval_event.set()
        self._interval_event = threading.Event()

    def is_running(self, *args, **kwargs) -> bool:
        """Whether scheduler is running."""
        return self._running

    def _update_thread(self):
        # wait a little
        self._abort_event.wait(10)

        # run forever
        while not self._abort_event.is_set():
            # not running?
            if self._running is False:
                self._abort_event.wait(10)
                continue

            # update scheduler
            try:
                self._scheduler(self.observer)
            except:
                log.exception('The scheduler threw an exception.')

            # sleep a little
            self._interval_event.wait(self._interval)


__all__ = ['Scheduler']
