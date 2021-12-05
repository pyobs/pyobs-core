import logging
from typing import Any, Optional

from pyobs.modules import Module
from pyobs.events import LogEvent, Event
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class FluentLogger(Module):
    """Log to fluentd server."""
    __module__ = 'pyobs.modules.utils'

    def __init__(self, hostname: str, port: int, *args: Any, **kwargs: Any):
        """Initialize a new logger.

        Args:
            hostname: Hostname of server.
            port: Port of server.

        """
        from fluent import sender
        Module.__init__(self, **kwargs)

        # store
        self._hostname = hostname
        self._port = port
        self._fluent: Optional[sender.FluentSender] = None

    async def open(self) -> None:
        """Open module."""
        from fluent import sender
        await Module.open(self)

        # get handler
        self._fluent = sender.FluentSender('pyobs', host=self._hostname, port=self._port)

        # listen to log events
        await self.comm.register_event(LogEvent, self._process_log_entry)

    def _process_log_entry(self, event: Event, sender: str) -> bool:
        """Process a new log entry.

        Args:
            event: The log event.
            sender: Name of sender.
        """

        # check
        if self._fluent is None:
            raise ValueError('Module not opened.')
        if not isinstance(event, LogEvent):
            raise ValueError('Wrong event type.')

        # get time
        time = Time(event.time).unix

        # send it
        self._fluent.emit_with_time(sender, time, event.data)
        return True


__all__ = ['FluentLogger']
