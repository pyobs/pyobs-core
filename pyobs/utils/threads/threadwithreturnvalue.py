from threading import Thread
import logging


log = logging.getLogger(__name__)


class ThreadWithReturnValue(Thread):
    def __init__(self, *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self._return = None
        self._exception = None

    def run(self):
        if self._target is not None:
            try:
                # save return valie
                self._return = self._target(*self._args, **self._kwargs)
            except Exception as e:
                # save exception, if one was caught
                self._exception = e

    def join(self, timeout=None):
        if timeout == 0.:
            log.warning('Joining thread with timeout of 0s. Is this correct?')
        # join thread
        Thread.join(self, timeout=timeout)
        # raise exception, if one was raised
        if self._exception is not None:
            raise self._exception
        # otherwise return value
        return self._return


__all__ = ['ThreadWithReturnValue']
