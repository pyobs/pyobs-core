from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any, TypeVar

_T = TypeVar("_T")

# single worker: evaluate_constraints_and_merits calls are always awaited sequentially by the
# caller (never fired concurrently), and DataProvider's functools.cache is not safe under real
# concurrent access -- one worker keeps that access serialized while still freeing the main loop.
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pyobs-scheduler")


async def run_cpu_bound(coro_fn: Callable[..., Coroutine[Any, Any, _T]], *args: object) -> _T:
    """Runs an async callable to completion on a dedicated worker thread, off the caller's loop.

    Args:
        coro_fn: An async callable whose body does not itself need to run on the caller's
            event loop (no dependency on the caller's other tasks, timers, or comm state).
        args: Positional args for coro_fn.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, lambda: asyncio.run(coro_fn(*args)))


__all__ = ["run_cpu_bound"]
