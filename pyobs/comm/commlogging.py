import logging
import os
from typing import TYPE_CHECKING, Any

from pyobs.events import LogEvent

if TYPE_CHECKING:
    from pyobs.comm import Comm


class CommLoggingHandler(logging.Handler):
    """A logging handler that sends all messages through a Comm module."""

    def __init__(self, comm: "Comm"):
        """Create a new logging handler.

        Args:
            comm: Comm module to use.
        """
        logging.Handler.__init__(self)
        self._comm = comm

        # get formatter
        self._formatter = logging.Formatter()

    def emit(self, rec: Any) -> None:
        """Send a new log entry to the comm module.

        Args:
            rec: Log record to send.
        """

        # format message
        msg = self._formatter.format(rec)

        # create and send event
        entry = LogEvent(rec.created, rec.levelname, os.path.basename(rec.pathname), rec.funcName, rec.lineno, msg)
        self._comm.log_message(entry)


__all__ = ["CommLoggingHandler"]
