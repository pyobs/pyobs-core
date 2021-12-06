import contextlib
import time
import asyncio
import inspect
from typing import TypeVar, Optional, List, Any, cast

from pyobs.utils.types import cast_response_to_real


async def event_wait(evt: asyncio.Event, timeout: float = 1.) -> bool:
    # suppress TimeoutError because we'll return False in case of timeout
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(evt.wait(), timeout)
    return evt.is_set()


async def acquire_lock(lock: asyncio.Lock, timeout: float = 1.) -> bool:
    # suppress TimeoutError because we'll return False in case of timeout
    try:
        await asyncio.wait_for(lock.acquire(), timeout)
        return True
    except asyncio.TimeoutError:
        return False


class Future(asyncio.Future):
    def __init__(self, empty: bool = False, signature: Optional[inspect.Signature] = None, *args, **kwargs):
        asyncio.Future.__init__(self, *args, **kwargs)

        """Init new base future."""
        self.timeout: Optional[float] = None
        self.signature: Optional[inspect.Signature] = signature

        # already set?
        if empty:
            # fire event
            self.set_result(None)

    def set_timeout(self, timeout: float) -> None:
        """
        Sets a new timeout for the method call.
        """
        self.timeout = timeout

    def get_timeout(self) -> Optional[float]:
        """
        Returns async timeout.
        """
        return self.timeout

    def _wait_for_time(self, timeout: float = 0):
        """Waits a little.

        Args:
            time: Time to wait in seconds.
        """
        start = time.time()
        while not self.done() or time.time() - start > timeout:
            return
        raise TimeoutError

    def __await__(self):
        # not finished? need to wait.
        if not self.done():
            try:
                # wait some 10s first
                self._wait_for_time(10)

            except TimeoutError:
                # got an additional timeout?
                if self.timeout is not None and self.timeout > 10:
                    # we already waited 10s, so subtract it
                    self._wait_for_time(self.timeout - 10.)

        # call parent
        result = asyncio.Future.__await__(self)
        print(result)

        # all ok, return value
        if self.signature is not None:
            # cast response to real types
            return cast_response_to_real(result, self.signature)
        else:
            return result

    @staticmethod
    async def wait_all(futures: List['BaseFuture']) -> List[Any]:
        return [await fut.wait() for fut in futures if fut is not None]


__all__ = ['Future']
