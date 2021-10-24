import logging
import threading
from typing import Any, TypeVar, Optional, List, Dict
from astroplan import Observer

from pyobs.comm import Comm
from pyobs.robotic import TaskArchive

log = logging.getLogger(__name__)


ProxyClass = TypeVar('ProxyClass')


class Script:
    def __init__(self, configuration: Any, task_archive: TaskArchive, comm: Comm, observer: Observer, **kwargs: Any):
        """Init Script.

        Args:
            comm: Comm object to use
            observer: Observer to use
        """
        self.exptime_done = 0.
        self.configuration = configuration
        self.task_archive = task_archive
        self.comm = comm
        self.observer = observer

    def can_run(self) -> bool:
        """Whether this config can currently run."""
        raise NotImplementedError

    def run(self, abort_event: threading.Event) -> None:
        """Run script.

        Args:
            abort_event: Event to abort run.

        Raises:
            InterruptedError: If interrupted
        """
        raise NotImplementedError

    def _check_abort(self, abort_event: threading.Event) -> None:
        """Check, whether we can continue with script.

        Args:
            abort_event: Event to abort run.

        Raises:
            InterruptedError: If interrupted
        """

        if abort_event.is_set() or not self.can_run():
            raise InterruptedError

    def get_fits_headers(self, namespaces: Optional[List[str]] = None) -> Dict[str, Any]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        return {}


__all__ = ['Script']
