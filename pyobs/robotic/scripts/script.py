import logging
import threading

log = logging.getLogger(__name__)


class Script:
    def can_run(self) -> bool:
        """Whether this config can currently run."""
        raise NotImplementedError

    def run(self, abort_event: threading.Event) -> int:
        """Run script.

        Args:
            abort_event: Event to abort run.

        Returns:
            Total exposure time in ms.
        """
        raise NotImplementedError


__all__ = ['Script']
