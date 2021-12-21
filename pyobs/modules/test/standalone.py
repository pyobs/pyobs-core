import asyncio
import logging
from typing import Any

from pyobs.modules import Module


log = logging.getLogger(__name__)


class StandAlone(Module):
    """Example module that only logs the given message forever in the given interval."""
    __module__ = 'pyobs.modules.test'

    def __init__(self, message: str = 'Hello world', interval: int = 10, **kwargs: Any):
        """Creates a new StandAlone object.

        Args:
            message: Message to log in the given interval.
            interval: Interval between messages.
        """
        Module.__init__(self, **kwargs)

        # add thread func
        self.add_background_task(self._message_func)

        # store
        self._message = message
        self._interval = interval

    async def _message_func(self):
        """Thread function for async processing."""
        # loop until closing
        while True:
            # log message
            log.info(self._message)

            # sleep a little
            await asyncio.sleep(self._interval)


__all__ = ['StandAlone']
