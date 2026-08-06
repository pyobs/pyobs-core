from __future__ import annotations

import threading

import pytest

from pyobs.robotic.scheduler._executor import run_cpu_bound


@pytest.mark.asyncio
async def test_run_cpu_bound_returns_value() -> None:
    async def add(a: int, b: int) -> int:
        return a + b

    result = await run_cpu_bound(add, 2, 3)
    assert result == 5


@pytest.mark.asyncio
async def test_run_cpu_bound_runs_on_different_thread() -> None:
    caller_thread = threading.get_ident()

    async def get_thread_ident() -> int:
        return threading.get_ident()

    worker_thread = await run_cpu_bound(get_thread_ident)
    assert worker_thread != caller_thread


@pytest.mark.asyncio
async def test_run_cpu_bound_propagates_exception() -> None:
    class MyError(ValueError):
        pass

    async def boom() -> None:
        raise MyError("something broke")

    with pytest.raises(MyError, match="something broke"):
        await run_cpu_bound(boom)
