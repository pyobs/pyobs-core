import logging

from pytel import PytelModule


log = logging.getLogger(__name__)


class StandAlone(PytelModule):
    """Example module without connectivity."""

    def __init__(self, message: str = 'Hello world', interval: int = 10, *args, **kwargs):
        """Creates a new StandAlone object.

        Args:
            message: Message to log in the given interval.
            interval: Interval between messages.
        """
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
