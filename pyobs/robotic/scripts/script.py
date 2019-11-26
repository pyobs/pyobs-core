import logging
import threading

log = logging.getLogger(__name__)


class Script:
    def __init__(self, *args, **kwargs):
        self.exptime_done = 0

    def can_run(self) -> bool:
        """Whether this config can currently run."""
        raise NotImplementedError

    def run(self, abort_event: threading.Event):
        """Run script.

        Args:
            abort_event: Event to abort run.

        Raises:
            InterruptedError: If interrupted
        """
        raise NotImplementedError

    def _check_abort(self, abort_event: threading.Event):
        """Check, whether we can continue with script.

        Args:
            abort_event: Event to abort run.

        Raises:
            InterruptedError: If interrupted
        """

        if abort_event.is_set() or not self.can_run():
            raise InterruptedError


__all__ = ['Script']
