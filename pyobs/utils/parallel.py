from __future__ import annotations

import asyncio
import contextlib
from asyncio import Task
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Any

from pyobs.utils.types import cast_response_to_real

if TYPE_CHECKING:
    from pyobs.comm import Comm


async def event_wait(evt: asyncio.Event, timeout: float = 1.0) -> bool:
    # suppress TimeoutError because we'll return False in case of timeout
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(evt.wait(), timeout)
    return evt.is_set()


async def acquire_lock(lock: asyncio.Lock, timeout: float = 1.0) -> bool:
    # suppress TimeoutError because we'll return False in case of timeout
    try:
        await asyncio.wait_for(lock.acquire(), timeout)
        return True
    except TimeoutError:
        return False


class Future(asyncio.Future[Any]):
    def __init__(
        self,
        empty: bool = False,
        annotation: dict[str, Any] | None = None,
        comm: Comm | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        asyncio.Future.__init__(self, *args, **kwargs)

        """Init new base future."""
        self.timeout: float | None = None
        self.annotation = annotation
        self.comm = comm

        # bookkeeping for (re-)scheduling the timeout while awaiting
        self._wait_loop: asyncio.AbstractEventLoop | None = None
        self._wait_start: float | None = None
        self._timeout_handle: asyncio.TimerHandle | None = None

        # already set?
        if empty:
            # fire event
            self.set_result(None)

    def set_timeout(self, timeout: float) -> None:
        """
        Sets a new timeout for the method call.
        """
        self.timeout = timeout

        # if we're already waiting, reschedule the pending timeout with the new value
        if self._wait_loop is not None and self._wait_start is not None and not self.done():
            if self._timeout_handle is not None:
                self._timeout_handle.cancel()
            remaining = max(0.0, self._wait_start + timeout - self._wait_loop.time())
            self._timeout_handle = self._wait_loop.call_later(remaining, self._on_timeout)

    def get_timeout(self) -> float | None:
        """
        Returns async timeout.
        """
        return self.timeout

    def __await__(self) -> Any:
        # not finished? need to wait.
        if not self.done():
            self._wait_loop = asyncio.get_running_loop()
            self._wait_start = self._wait_loop.time()

            # schedule timeout
            timeout = self.timeout if self.timeout is not None else 10.0
            self._timeout_handle = self._wait_loop.call_later(timeout, self._on_timeout)

            self._asyncio_future_blocking = True
            yield self  # suspend until done or timeout

            if self._timeout_handle is not None:
                self._timeout_handle.cancel()  # cancel timeout if completed normally

        # still not done? raise exception.
        if not self.done():
            raise RuntimeError("await wasn't used with future")

        # get result
        result = self.result()

        # all ok, return value
        if self.annotation and self.comm:
            result = cast_response_to_real(
                result, self.annotation["return"], self.comm.cast_to_real_pre, self.comm.cast_to_real_post
            )
        return result

    @staticmethod
    async def wait_all(futures: list[Future | Coroutine[Any, Any, Any] | Task[Any] | None]) -> list[Any]:
        return [await fut for fut in futures if fut is not None]

    def _on_timeout(self) -> None:
        if not self.done():
            self.set_exception(TimeoutError())


__all__ = ["Future", "event_wait", "acquire_lock"]
