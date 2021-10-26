import threading
from threading import Event
from typing import Tuple, TYPE_CHECKING, Any, Optional, List, Dict

from astroplan import Observer

from pyobs.comm import Comm
from pyobs.utils.time import Time
if TYPE_CHECKING:
    from pyobs.robotic.taskarchive import TaskArchive


class Task:
    def __init__(self, tasks: 'TaskArchive', comm: Comm, observer: Observer, **kwargs: Any):
        self.task_archive = tasks
        self.comm = comm
        self.observer = observer

    @property
    def id(self) -> Any:
        """ID of task."""
        raise NotImplementedError

    @property
    def name(self) -> str:
        """Returns name of task."""
        raise NotImplementedError

    @property
    def duration(self) -> float:
        """Returns estimated duration of task in seconds."""
        raise NotImplementedError

    @property
    def start(self) -> Time:
        """Start time for task"""
        raise NotImplementedError

    @property
    def end(self) -> Time:
        """End time for task"""
        raise NotImplementedError

    def can_run(self) -> bool:
        """Checks, whether this task could run now.

        Returns:
            True, if task can run now.
        """
        raise NotImplementedError

    @property
    def can_start_late(self) -> bool:
        """Whether this tasks is allowed to start later than the user-set time, e.g. for flatfields.

        Returns:
            True, if task can start late.
        """
        raise NotImplementedError

    def run(self, abort_event: Event) -> None:
        """Run a task

        Args:
            abort_event: Event to be triggered to abort task.
        """
        raise NotImplementedError

    def is_finished(self) -> bool:
        """Whether task is finished."""
        raise NotImplementedError

    def get_fits_headers(self, namespaces: Optional[List[str]] = None) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        return {}

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
