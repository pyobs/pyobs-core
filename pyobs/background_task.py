import asyncio
import logging
from typing import Optional, Coroutine, Any, Callable

from pyobs.utils.exceptions import SevereError

log = logging.getLogger(__name__)


class BackgroundTask:
    def __init__(self, func: Callable[..., Coroutine[Any, Any, None]], restart: bool) -> None:
        self._func: Callable[..., Coroutine[Any, Any, None]] = func
        self._restart: bool = restart
        self._task: Optional[asyncio.Future] = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._func())
        self._task.add_done_callback(self._callback_function)

    def _callback_function(self, args=None) -> None:
        try:
            exception = self._task.exception()
        except asyncio.CancelledError:
            return

        if isinstance(exception, SevereError):
            raise exception
        elif exception is not None:
            log.exception("Exception in task %s.", self._func.__name__)

        if self._restart:
            log.error("Background task for %s has died, restarting...", self._func.__name__)
            self.start()
        else:
            log.error("Background task for %s has died, quitting...", self._func.__name__)

    def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
