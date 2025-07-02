from threading import Thread
import logging
from typing import Optional, Any

log = logging.getLogger(__name__)


class ThreadWithReturnValue(Thread):
    def __init__(self, *args: Any, **kwargs: Any):
        Thread.__init__(self, *args, **kwargs)
        self._return: Optional[Any] = None
        self._exception: Optional[Exception] = None

    def run(self) -> None:
        if self._target is not None:
            try:
                # save return valie
                self._return = self._target(*self._args, **self._kwargs)
            except Exception as e:
                # save exception, if one was caught
                self._exception = e

    def join(self, timeout: Optional[float] = None) -> Any:
        if timeout is None:
            log.warning("Joining thread with timeout of 0s. Is this correct?")
        # join thread
        Thread.join(self, timeout=timeout)
        # raise exception, if one was raised
        if self._exception is not None:
            raise self._exception
        # otherwise return value
        return self._return


__all__ = ["ThreadWithReturnValue"]
