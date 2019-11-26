import threading
from threading import Event

from pyobs.utils.time import Time


class Task:
    def __init__(self, scheduler: 'Scheduler', *args, **kwargs):
        self.scheduler = scheduler

    def name(self) -> str:
        """Returns name of task.

        Returns:
            Name of task.
        """
        raise NotImplementedError

    def window(self) -> (Time, Time):
        """Returns the time window for this task.

        Returns:
            Start and end time for this observation window.
        """
        raise NotImplementedError

    def can_run(self) -> bool:
        """Checks, whether this task could run now.

        Returns:
            True, if task can run now.
        """
        raise NotImplementedError

    def run(self, abort_event: Event):
        """Run a task

        Args:
            abort_event: Event to be triggered to abort task.
        """
        raise NotImplementedError

    def is_finished(self) -> bool:
        """Whether task is finished."""
        raise NotImplementedError

    def get_fits_headers(self, namespaces: list = None) -> dict:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        raise NotImplementedError

    @staticmethod
    def _check_abort(abort_event: threading.Event, end: Time = None):
        """Throws an exception, if abort_event is set or window has passed

        Args:
            abort_event: Event to check
            end: End of observing window for task

        Raises:
            InterruptedError: if task should be aborted
        """

        # check abort event
        if abort_event.is_set():
            raise InterruptedError

        # check time
        if end is not None and end < Time.now():
            raise InterruptedError


__all__ = ['Task']
