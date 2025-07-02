import asyncio
import logging
from typing import Any

from pyobs.utils.parallel import acquire_lock

log = logging.getLogger(__name__)


class AcquireLockFailed(Exception):
    pass


class LockWithAbort(object):
    """Tries to acquire a lock. If unsuccessful, it sets the event and tries again."""

    def __init__(self, lock: asyncio.Lock, event: asyncio.Event):
        self.lock = lock
        self.event = event
        self.acquired = False

    async def __aenter__(self) -> None:
        # first try to acquire lock without timeout
        self.acquired = await acquire_lock(self.lock)

        # not successful?
        if not self.acquired:
            # could not acquire lock, so set abort_event
            self.event.set()

            # try to acquire again with a timeout
            self.acquired = await acquire_lock(self.lock, 10.0)

            # still not successful?
            if not self.acquired:
                # raise exception
                raise AcquireLockFailed()

        # got lock, so unset abort and remember that we were successful
        self.event.clear()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # if we acquired the lock, we release it again here
        if self.acquired:
            self.lock.release()
            self.acquired = False


__all__ = ["LockWithAbort", "AcquireLockFailed"]
