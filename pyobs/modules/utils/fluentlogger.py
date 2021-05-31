import io
import logging
from enum import Enum
from inspect import Parameter
from pprint import pprint
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CallbackContext

from pyobs.modules import Module
from pyobs.events import LogEvent
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class FluentLogger(Module):
    """Log to fluentd server."""
    __module__ = 'pyobs.modules.utils'

    def __init__(self, hostname: str, port: int, *args, **kwargs):
        """Initialize a new logger.

        Args:
            hostname: Hostname of server.
            port: Port of server.

        """
        Module.__init__(self, *args, **kwargs)

        # store
        self._hostname = hostname
        self._port = port
        self._fluent = None

    def open(self):
        """Open module."""
        from fluent import sender
        Module.open(self)

        # get handler
        self._fluent = sender.FluentSender('pyobs', host=self._hostname, port=self._port)

        # listen to log events
        self.comm.register_event(LogEvent, self._process_log_entry)

    def _process_log_entry(self, entry: LogEvent, sender: str):
        """Process a new log entry.

        Args:
            entry: The log event.
            sender: Name of sender.
        """

        # get time
        time = Time(entry.time).unix

        # send it
        self._fluent.emit_with_time(sender, time, entry.data)


__all__ = ['FluentLogger']
