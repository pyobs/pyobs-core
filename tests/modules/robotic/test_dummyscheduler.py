from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import astropy.units as u
import pytest

from pyobs.comm import Comm
from pyobs.interfaces import IRoboticScheduler, IRunning
from pyobs.modules.robotic import DummyScheduler
from pyobs.utils.time import Time


def make_scheduler(**kwargs) -> DummyScheduler:
    return DummyScheduler(comm=MagicMock(spec=Comm), **kwargs)


def _state_for(mock: AsyncMock, interface: object) -> object:
    for call in reversed(mock.await_args_list):
        if call.args[0] is interface:
            return call.args[1]
    raise AssertionError(f"set_state was never called with {interface}")


# ── __init__ / _generate_schedule ────────────────────────────────────────────


def test_init_defaults() -> None:
    scheduler = make_scheduler()
    assert scheduler._running is True
    assert scheduler._last_reschedule is None
    assert scheduler._schedule == []
    assert scheduler._need_update is True


def test_generate_schedule_produces_contiguous_sorted_tasks() -> None:
    scheduler = make_scheduler(schedule_size=5, min_duration=10, max_duration=10)
    scheduler._generate_schedule()

    assert len(scheduler._schedule) == 5
    for a, b in zip(scheduler._schedule, scheduler._schedule[1:]):
        assert a.end == b.start  # contiguous, in order
    ids = [t.id for t in scheduler._schedule]
    assert ids == sorted(ids)  # unique, increasing


# ── open / start / stop ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_publishes_state(mocker) -> None:
    from pyobs.modules import Module

    scheduler = make_scheduler(schedule_size=4)
    scheduler._comm.set_state = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())

    await scheduler.open()

    state = _state_for(scheduler._comm.set_state, IRunning)
    assert state.running is True
    # open() generates the first schedule synchronously (not left to the worker's first tick),
    # so get_schedule() has something to return immediately -- last_reschedule is already set
    state = _state_for(scheduler._comm.set_state, IRoboticScheduler)
    assert state.last_reschedule is not None
    assert len(scheduler._schedule) == 4


@pytest.mark.asyncio
async def test_start_sets_running() -> None:
    scheduler = make_scheduler()
    scheduler._running = False
    scheduler._comm.set_state = AsyncMock()

    await scheduler.start()

    assert scheduler._running is True
    state = _state_for(scheduler._comm.set_state, IRunning)
    assert state.running is True


@pytest.mark.asyncio
async def test_stop_clears_running() -> None:
    scheduler = make_scheduler()
    scheduler._comm.set_state = AsyncMock()

    await scheduler.stop()

    assert scheduler._running is False
    state = _state_for(scheduler._comm.set_state, IRunning)
    assert state.running is False


# ── run / _schedule_worker ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_triggers_reschedule() -> None:
    scheduler = make_scheduler()
    scheduler._need_update = False

    await scheduler.run()

    assert scheduler._need_update is True


@pytest.mark.asyncio
async def test_schedule_worker_generates_and_publishes(mocker) -> None:
    scheduler = make_scheduler(schedule_size=3)
    scheduler._comm.set_state = AsyncMock()

    call_count = 0

    async def fake_sleep(t: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 1:
            raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.robotic.dummyscheduler.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await scheduler._schedule_worker()

    assert len(scheduler._schedule) == 3
    assert scheduler._last_reschedule is not None
    state = _state_for(scheduler._comm.set_state, IRoboticScheduler)
    assert state.last_reschedule is not None


@pytest.mark.asyncio
async def test_schedule_worker_skips_when_not_running(mocker) -> None:
    scheduler = make_scheduler()
    scheduler._running = False
    scheduler._comm.set_state = AsyncMock()

    call_count = 0

    async def fake_sleep(t: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= 1:
            raise asyncio.CancelledError()

    mocker.patch("pyobs.modules.robotic.dummyscheduler.asyncio.sleep", side_effect=fake_sleep)

    with pytest.raises(asyncio.CancelledError):
        await scheduler._schedule_worker()

    assert scheduler._schedule == []
    scheduler._comm.set_state.assert_not_awaited()


# ── get_schedule ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_schedule_respects_limit() -> None:
    scheduler = make_scheduler(schedule_size=5, min_duration=10, max_duration=10)
    scheduler._generate_schedule()

    result = await scheduler.get_schedule(limit=2)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_schedule_caps_limit_at_hard_ceiling() -> None:
    scheduler = make_scheduler(schedule_size=DummyScheduler._MAX_SCHEDULE_LIMIT + 10)
    scheduler._generate_schedule()

    result = await scheduler.get_schedule(limit=10_000)

    assert len(result) == scheduler._MAX_SCHEDULE_LIMIT


@pytest.mark.asyncio
async def test_get_schedule_rejects_negative_limit() -> None:
    scheduler = make_scheduler()
    with pytest.raises(ValueError):
        await scheduler.get_schedule(limit=-1)


@pytest.mark.asyncio
async def test_get_schedule_drops_elapsed_tasks() -> None:
    scheduler = make_scheduler(schedule_size=3, min_duration=10, max_duration=10)
    scheduler._generate_schedule()
    scheduler._schedule[0].end = Time.now() - 10 * u.second

    result = await scheduler.get_schedule()

    assert len(result) == 2
    assert scheduler._schedule[0] not in result


@pytest.mark.asyncio
async def test_get_schedule_marks_current_task_in_progress() -> None:
    scheduler = make_scheduler(schedule_size=1, min_duration=100, max_duration=100)
    scheduler._generate_schedule()
    scheduler._schedule[0].start = Time.now() - 10 * u.second
    scheduler._schedule[0].end = Time.now() + 90 * u.second

    result = await scheduler.get_schedule()

    assert result[0].state == "in_progress"


@pytest.mark.asyncio
async def test_get_schedule_does_not_mutate_stored_tasks() -> None:
    scheduler = make_scheduler(schedule_size=1, min_duration=100, max_duration=100)
    scheduler._generate_schedule()
    scheduler._schedule[0].start = Time.now() - 10 * u.second
    scheduler._schedule[0].end = Time.now() + 90 * u.second

    await scheduler.get_schedule()

    assert scheduler._schedule[0].state == "pending"  # unchanged -- get_schedule returned a copy


@pytest.mark.asyncio
async def test_get_schedule_rejects_non_int_limit() -> None:
    scheduler = make_scheduler()
    with pytest.raises(ValueError):
        await scheduler.get_schedule(limit="20")  # type: ignore[arg-type]
