from __future__ import annotations
import asyncio
import logging
from typing import Any, TYPE_CHECKING
from collections.abc import Coroutine, Callable
import time

if TYPE_CHECKING:
    from pyobs.object import Object

log = logging.getLogger(__name__)


MAX_FINISH_INTERVAL_SECONDS = 10
MAX_FINISH_COUNT = 3


class BackgroundTask:
    def __init__(self, func: Callable[..., Coroutine[Any, Any, None]], restart: bool, parent: Object) -> None:
        self._func: Callable[..., Coroutine[Any, Any, None]] = func
        self._restart: bool = restart
        self._parent = parent
        self._task: asyncio.Future[Any] | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._func_wrapper())

    async def _func_wrapper(self) -> None:
        start = time.time()
        finish_count = 0

        while True:
            try:
                await self._func()
            except asyncio.CancelledError:
                log.info("Task %s was cancelled.", self._func.__name__)
                return
            except:
                log.exception("Exception in task %s.", self._func.__name__)

            # check time since last exit
            if time.time() - start < MAX_FINISH_INTERVAL_SECONDS:
                finish_count += 1
                if finish_count > MAX_FINISH_COUNT:
                    log.error("Succession of failure for background task %s too fast, quitting...", self._func.__name__)
                    if self._restart:
                        self._parent.quit()
                        return
                    else:
                        return
            else:
                start = time.time()
                finish_count = 0

            # don't restart?
            if self._restart:
                log.info("Background task for %s has died, restarting...", self._func.__name__)
            else:
                log.info("Background task for %s has died, quitting...", self._func.__name__)
                return

    def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
