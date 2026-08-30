from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm import Comm
from pyobs.events import TaskFailedEvent, TaskFinishedEvent, TaskStartedEvent
from pyobs.interfaces import IRobotic, IRunning
from pyobs.modules.robotic import DummyMastermind


def make_mastermind(**kwargs) -> DummyMastermind:
    return DummyMastermind(comm=MagicMock(spec=Comm), **kwargs)


def _state_for(mock: AsyncMock, interface: object) -> object:
    for call in reversed(mock.await_args_list):
        if call.args[0] is interface:
            return call.args[1]
    raise AssertionError(f"set_state was never called with {interface}")


def _states_for(mock: AsyncMock, interface: object) -> list[object]:
    return [call.args[1] for call in mock.await_args_list if call.args[0] is interface]


# ── __init__ ─────────────────────────────────────────────────────────────────


def test_init_defaults() -> None:
    mm = make_mastermind()
    assert mm._running is False
    assert mm._task is None


def test_make_task_produces_unique_increasing_ids() -> None:
    mm = make_mastermind()
    t1 = mm._make_task()
    t2 = mm._make_task()
    assert t1.id != t2.id
    assert t1.id < t2.id


# ── open / start / stop ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_open_publishes_running_and_robotic_state(mocker) -> None:
    from pyobs.modules import Module

    mm = make_mastermind()
    mm._comm.register_event = AsyncMock()
    mm._comm.set_state = AsyncMock()
    mocker.patch.object(Module, "open", AsyncMock())

    await mm.open()

    state = _state_for(mm._comm.set_state, IRunning)
    assert state.running is True
    state = _state_for(mm._comm.set_state, IRobotic)
    assert state.current is None
    assert state.next is None


@pytest.mark.asyncio
async def test_start_sets_running() -> None:
    mm = make_mastermind()
    mm._comm.set_state = AsyncMock()

    await mm.start()

    assert mm._running is True
    state = _state_for(mm._comm.set_state, IRunning)
    assert state.running is True


@pytest.mark.asyncio
async def test_stop_clears_running() -> None:
    mm = make_mastermind()
    mm._running = True
    mm._comm.set_state = AsyncMock()

    await mm.stop()

    assert mm._running is False
    state = _state_for(mm._comm.set_state, IRunning)
    assert state.running is False


# ── _run_thread ──────────────────────────────────────────────────────────────


async def _run_briefly(mm: DummyMastermind, mocker, iterations: int = 6) -> None:
    """Run _run_thread with the initial 5s delay and inter-loop sleeps collapsed."""
    call_count = 0
    real_sleep = asyncio.sleep

    async def fake_sleep(t: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= iterations:
            raise asyncio.CancelledError()
        await real_sleep(0)

    mocker.patch("pyobs.modules.robotic.dummymastermind.asyncio.sleep", side_effect=fake_sleep)
    with pytest.raises(asyncio.CancelledError):
        await mm._run_thread()


@pytest.mark.asyncio
async def test_run_thread_starts_and_finishes_a_task(mocker) -> None:
    mm = make_mastermind(blocked_probability=0.0, fail_probability=0.0)
    mm._running = True
    mm._comm.set_state = AsyncMock()
    mm._comm.send_event = AsyncMock()

    await _run_briefly(mm, mocker)

    started = [c.args[0] for c in mm._comm.send_event.await_args_list if isinstance(c.args[0], TaskStartedEvent)]
    finished = [c.args[0] for c in mm._comm.send_event.await_args_list if isinstance(c.args[0], TaskFinishedEvent)]
    assert len(started) >= 1
    assert len(finished) >= 1

    states = _states_for(mm._comm.set_state, IRobotic)
    assert any(s.current is not None for s in states)
    # some published state must show the task cleared again after finishing -- not necessarily
    # the *last* one, since a fast, unmocked-random loop may already be mid-way through a
    # second cycle by the time cancellation lands
    assert any(s.current is None for s in states)


@pytest.mark.asyncio
async def test_run_thread_simulates_blocked_reason(mocker) -> None:
    mm = make_mastermind(blocked_probability=1.0, min_blocked_duration=0.0, max_blocked_duration=0.0)
    mm._running = True
    mm._comm.set_state = AsyncMock()
    mm._comm.send_event = AsyncMock()

    await _run_briefly(mm, mocker, iterations=2)

    states = _states_for(mm._comm.set_state, IRobotic)
    assert any(s.cant_run_reason is not None and s.next is not None for s in states)


@pytest.mark.asyncio
async def test_run_thread_simulates_failure(mocker) -> None:
    mm = make_mastermind(blocked_probability=0.0, fail_probability=1.0)
    mm._running = True
    mm._comm.set_state = AsyncMock()
    mm._comm.send_event = AsyncMock()

    await _run_briefly(mm, mocker)

    failed = [c.args[0] for c in mm._comm.send_event.await_args_list if isinstance(c.args[0], TaskFailedEvent)]
    assert len(failed) >= 1


@pytest.mark.asyncio
async def test_run_thread_does_not_pick_up_new_task_while_stopped(mocker) -> None:
    mm = make_mastermind()
    mm._running = False
    mm._comm.set_state = AsyncMock()
    mm._comm.send_event = AsyncMock()

    await _run_briefly(mm, mocker)

    mm._comm.send_event.assert_not_awaited()
    assert mm._task is None
