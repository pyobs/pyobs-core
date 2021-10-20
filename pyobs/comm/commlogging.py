import logging
import os
from typing import TYPE_CHECKING

from pyobs.events import LogEvent
if TYPE_CHECKING:
    from pyobs.comm import Comm


class CommLoggingHandler(logging.Handler):
    """A logging handler that sends all messages through a Comm module."""

    def __init__(self, comm: 'Comm', *args, **kwargs):
        """Create a new logging handler.

        Args:
            comm: Comm module to use.
        """
        logging.Handler.__init__(self, *args, **kwargs)
        self._comm = comm

    def emit(self, rec):
        """Send a new log entry to the comm module.

        Args:
            rec: Log record to send.
        """
        entry = LogEvent(rec.created, rec.levelname, os.path.basename(rec.pathname), rec.funcName,  rec.lineno,
                         rec.msg % rec.args)
        self._comm.log_message(entry)


__all__ = ['CommLoggingHandler']
