import asyncio
import logging
from typing import Optional, Coroutine, Any, Callable

log = logging.getLogger(__name__)


class BackgroundTask:
    def __init__(self, func: Callable[..., Coroutine[Any, Any, None]], restart: bool) -> None:
        self._func: Callable[..., Coroutine[Any, Any, None]] = func
        self._restart: bool = restart
        self._task: Optional[asyncio.Future] = None

    def start(self) -> None:
        self._start_task()

    def _callback_function(self, args=None) -> None:
        try:
            exception = self._task.exception()
        except asyncio.CancelledError:
            return

        if exception is not None:
            log.exception("Exception in thread method %s." % self._func.__name__)

        if self._restart:
            log.error("Background task for %s has died, restarting...", self._func.__name__)
            self._start_task()
        else:
            log.error("Background task for %s has died, quitting...", self._func.__name__)

    def _start_task(self) -> None:
        self._task = asyncio.create_task(self._func())
        self._task.add_done_callback(self._callback_function)

    def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
