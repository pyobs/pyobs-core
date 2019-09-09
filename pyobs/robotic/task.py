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

    def run(self, abort_event: Event):
        """Run a task

        Args:
            abort_event: Event to be triggered to abort task.
        """
        raise NotImplementedError

    def is_finished(self) -> bool:
        """Whether task is finished."""
        raise NotImplementedError

    def get_fits_headers(self) -> dict:
        """Return FITS header produced by this task.

        Returns:
            Dictionary with FITS headers.
        """
        raise NotImplementedError


__all__ = ['Task']
