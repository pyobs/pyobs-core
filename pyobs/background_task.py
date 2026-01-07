import asyncio
import logging
from typing import Coroutine, Any, Callable
import time

log = logging.getLogger(__name__)


MAX_FINISH_INTERVAL_SECONDS = 10
MAX_FINISH_COUNT = 3


class BackgroundTask:
    def __init__(self, func: Callable[..., Coroutine[Any, Any, None]], restart: bool) -> None:
        self._func: Callable[..., Coroutine[Any, Any, None]] = func
        self._restart: bool = restart
        self._task: asyncio.Future[Any] | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._func_wrapper())

    async def _func_wrapper(self):
        start = time.time()
        finish_count = 0

        while True:
            try:
                await self._func()
            except asyncio.CancelledError:
                log.info(f"Task {self._func.__name__} was cancelled.")
                return
            except:
                log.exception(f"Exception in task {self._func.__name__}.")

            # check time since last exit
            if time.time() - start < MAX_FINISH_INTERVAL_SECONDS:
                finish_count += 1
                if finish_count > MAX_FINISH_COUNT:
                    log.error(f"Succession of failure for background task {self._func.__name__} too fast, quitting...")
                    if self._restart:
                        # todo: quit pyobs here
                        return
                    else:
                        return
            else:
                start = time.time()
                finish_count = 0

            # don't restart?
            if self._restart:
                log.info(f"Background task for {self._func.__name__} has died, restarting...")
            else:
                log.info(f"Background task for {self._func.__name__} has died, quitting...")
                return

    def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
