import logging

from pyobs import PyObsModule


log = logging.getLogger(__name__)


class StandAlone(PyObsModule):
    """Example module that only logs the given message forever in the given interval."""

    def __init__(self, message: str = 'Hello world', interval: int = 10, *args, **kwargs):
        """Creates a new StandAlone object.

        Args:
            message: Message to log in the given interval.
            interval: Interval between messages.
        """
        PyObsModule.__init__(self, thread_funcs=self._message, *args, **kwargs)

        # store
        self._message = message
        self._interval = interval

    def _message(self):
        """Thread function for async processing."""
        # loop until closing
        while not self.closing.is_set():
            # log message
            log.info(self._message)

            # sleep a little
            self.closing.wait(self._interval)


__all__ = ['StandAlone']
