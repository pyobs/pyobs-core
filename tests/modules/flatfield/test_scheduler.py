from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm import Comm
from pyobs.interfaces import IBinning, IFilters, IFlatField
from pyobs.modules.flatfield.scheduler import FlatFieldScheduler
from pyobs.robotic.utils.skyflats.priorities.base import SkyflatPriorities
from pyobs.robotic.utils.skyflats.scheduler import Scheduler, SchedulerItem
from tests.helpers import make_proxy_cm


def make_scheduler_module(**kwargs) -> FlatFieldScheduler:
    comm = MagicMock(spec=Comm)
    priorities = AsyncMock(spec=SkyflatPriorities)
    module = FlatFieldScheduler(
        flatfield="flatfield",
        functions={"clear": "1.0"},
        priorities=priorities,
        comm=comm,
        **kwargs,
    )
    module._scheduler = AsyncMock(spec=Scheduler)
    return module


def setup_flatfield_proxy(module: FlatFieldScheduler, flatfield: MagicMock) -> None:
    def proxy_se(name: object, iface: object = None) -> MagicMock:
        return make_proxy_cm(flatfield)

    module._comm.proxy = MagicMock(side_effect=proxy_se)


# ── open ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_checks_flatfield_proxy(mocker) -> None:
    from pyobs.modules import Module

    module = make_scheduler_module()
    module._comm.has_proxy = AsyncMock(return_value=True)
    mocker.patch.object(Module, "open", AsyncMock())

    await module.open()

    module._comm.has_proxy.assert_awaited_once_with("flatfield", IFlatField)


# ── run ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_raises_when_already_running() -> None:
    module = make_scheduler_module()

    block = asyncio.Event()

    async def blocking_call(*args: object, **kwargs: object) -> None:
        await block.wait()

    module._scheduler.side_effect = blocking_call
    module._scheduler.__iter__ = lambda self: iter([])

    task = asyncio.create_task(module.run())
    await asyncio.sleep(0.05)

    with pytest.raises(ValueError):
        await module.run()

    block.set()
    await task


@pytest.mark.asyncio
async def test_run_schedules_and_executes_items(mocker) -> None:
    async def fast_event_wait(evt: asyncio.Event, timeout: float = 1.0) -> bool:
        await asyncio.sleep(0)
        return evt.is_set()

    mocker.patch("pyobs.modules.flatfield.scheduler.event_wait", side_effect=fast_event_wait)

    module = make_scheduler_module(count=7)
    item = SchedulerItem(start=0, end=1, filter_name="clear", binning=(2, 2), priority=1.0)
    module._scheduler.__iter__ = lambda self: iter([item])

    flatfield = MagicMock(spec=[IFilters, IBinning, IFlatField])
    flatfield.set_filter = AsyncMock()
    flatfield.set_binning = AsyncMock()
    flatfield.flat_field = AsyncMock(return_value=(7, 30.0))
    setup_flatfield_proxy(module, flatfield)

    await module.run()

    module._scheduler.assert_awaited_once()
    flatfield.set_filter.assert_awaited_once_with("clear")
    flatfield.set_binning.assert_awaited_once_with(2, 2)
    flatfield.flat_field.assert_awaited_once_with(7)


@pytest.mark.asyncio
async def test_run_aborts_current_flat_field_when_requested(mocker) -> None:
    async def fast_event_wait(evt: asyncio.Event, timeout: float = 1.0) -> bool:
        await asyncio.sleep(0.01)
        return evt.is_set()

    mocker.patch("pyobs.modules.flatfield.scheduler.event_wait", side_effect=fast_event_wait)

    module = make_scheduler_module()
    item = SchedulerItem(start=0, end=1, filter_name="clear", binning=(1, 1), priority=1.0)
    module._scheduler.__iter__ = lambda self: iter([item])

    never_finishes = asyncio.Event()

    async def blocking_flat_field(count: int) -> tuple[int, float]:
        await never_finishes.wait()
        return 0, 0.0

    flatfield = MagicMock(spec=[IFilters, IBinning, IFlatField])
    flatfield.set_filter = AsyncMock()
    flatfield.set_binning = AsyncMock()
    flatfield.flat_field = AsyncMock(side_effect=blocking_flat_field)
    flatfield.abort = AsyncMock(side_effect=lambda **kw: never_finishes.set())
    setup_flatfield_proxy(module, flatfield)

    task = asyncio.create_task(module.run())
    await asyncio.sleep(0.05)
    await module.abort()
    await asyncio.wait_for(task, timeout=5)

    flatfield.abort.assert_awaited()


# ── abort ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_abort_sets_event() -> None:
    module = make_scheduler_module()
    assert not module._abort.is_set()
    await module.abort()
    assert module._abort.is_set()
