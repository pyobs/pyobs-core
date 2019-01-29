"""
The StandAlone module is an example, showing the most simple module implementation without any connectivity.
It just logs a given message continuously with a given interval.


Configuration
-------------

message (str) = Hello world
    The message that should be logged.

interval (int) = 5
    The interval in seconds between logging messages.
"""

import logging

from pytel import PytelModule


log = logging.getLogger(__name__)


class StandAlone(PytelModule):
    """Example module without connectivity."""

    def __init__(self, message: str = 'Hello world', interval: int = 10, *args, **kwargs):
        """Creates a new StandAlone object."""
        PytelModule.__init__(self, thread_funcs=self._message, *args, **kwargs)

        # store
        self._message = message
        self._interval = interval

    def open(self) -> bool:
        """Open module."""
        return PytelModule.open(self)

    def close(self):
        """Close module."""
        PytelModule.close(self)

    def _message(self):
        """Thread function for async processing."""
        # loop until closing
        while not self.closing.is_set():
            # log message
            log.info(self._message)

            # sleep a little
            self.closing.wait(self._interval)


__all__ = ['StandAlone']
