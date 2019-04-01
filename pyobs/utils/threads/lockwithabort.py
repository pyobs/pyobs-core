import logging


log = logging.getLogger(__name__)


class AcquireLockFailed(Exception):
    pass


class LockWithAbort(object):
    """Tries to acquire a lock. If unsuccessful, it sets the event and tries again."""
    def __init__(self, lock, event):
        self.lock = lock
        self.event = event
        self.acquired = False

    def __enter__(self):
        # first try to acquire lock without timeout
        self.acquired = self.lock.acquire(timeout=0.)

        # not successful?
        if not self.acquired:
            # could not acquire lock, so set abort_event
            self.event.set()

            # try to acquire again with a timeout
            self.acquired = self.lock.acquire(timeout=10.)

            # still not successful?
            if not self.acquired:
                # raise exception
                raise AcquireLockFailed()

        # got lock, so unset abort and remember that we were successful
        self.event.clear()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # if we acquired the lock, we release it again here
        if self.acquired:
            self.lock.release()
            self.acquired = False


__all__ = ['LockWithAbort', 'AcquireLockFailed']
