from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import astropy.units as u
import pytest

from pyobs.comm import Comm
from pyobs.events import TaskSkippedEvent
from pyobs.interfaces import FitsHeaderEntry
from pyobs.modules.robotic.mastermind import Mastermind
from pyobs.robotic import Observation, ObservationArchive, ObservationState
from pyobs.robotic.task import Task
from pyobs.robotic.taskrunner import TaskRunner
from pyobs.utils.time import Time


def make_mastermind(**kwargs) -> Mastermind:
    comm = MagicMock(spec=Comm)
    schedule = MagicMock(spec=ObservationArchive)
    runner = MagicMock(spec=TaskRunner)
    return Mastermind(comm=comm, schedule=schedule, runner=runner, **kwargs)


@pytest.mark.asyncio
async def test_get_fits_header_before_no_task_returns_empty() -> None:
    mm = make_mastermind()
    assert await mm.get_fits_header_before() == {}


@pytest.mark.asyncio
async def test_get_fits_header_before_includes_version_headers(mocker) -> None:
    mocker.patch(
        "pyobs.modules.robotic.mastermind.version_fits_headers",
        return_value={"HIERARCH TESTMASTERMIND VERSION PYOBS-CORE": FitsHeaderEntry("2.4.1", "")},
    )
    mm = make_mastermind()
    mm._task = Task(id=1, name="task1")

    hdr = await mm.get_fits_header_before()

    assert hdr["HIERARCH TESTMASTERMIND VERSION PYOBS-CORE"].value == "2.4.1"


# ── _same_observation ────────────────────────────────────────────────────────


def make_observation(task: Task, start: Time | None = None, duration: float = 1800.0) -> Observation:
    if start is None:
        start = Time.now() - 10.0 * u.minute
    return Observation(task=task, start=start, end=start + duration * u.second, state=ObservationState.PENDING)


def test_same_observation_none_never_matches() -> None:
    assert Mastermind._same_observation(None, make_observation(Task(id=1, name="a"))) is False


def test_same_observation_matches_task_and_window() -> None:
    task = Task(id=1, name="a")
    start = Time("2026-09-10T22:00:00", scale="utc")
    a = make_observation(task, start)

    assert Mastermind._same_observation(a, make_observation(task, start)) is True
    assert Mastermind._same_observation(a, make_observation(task, start + 1 * u.second)) is False
    assert Mastermind._same_observation(a, make_observation(Task(id=2, name="a"), start)) is False


# ── TaskSkippedEvent emission ────────────────────────────────────────────────


class LateStartTask(Task):
    """Task that may start after its scheduled time."""

    @property
    def can_start_late(self) -> bool:
        return True


def _prepare(mm: Mastermind, observations: list[Observation]) -> None:
    """Wire up mocks so _run_thread can be driven through the late-start-skip branch."""
    mm._running = True
    mm._comm.set_state = AsyncMock()
    mm._comm.send_event = AsyncMock()
    mm._observation_archive.update_observation = AsyncMock()
    mm._task_runner.can_run = AsyncMock(return_value=True)
    mm._task_runner.run_task = AsyncMock()

    calls = {"n": 0}

    def _next_observation(*args, **kwargs) -> Observation:
        i = min(calls["n"], len(observations) - 1)
        calls["n"] += 1
        return observations[i]

    mm._observation_archive.get_next_observation = AsyncMock(side_effect=_next_observation)


async def _run_briefly(mm: Mastermind, mocker, iterations: int = 8) -> None:
    """Run _run_thread with the initial 5s delay and inter-loop sleeps collapsed."""
    call_count = 0
    real_sleep = asyncio.sleep

    async def fake_sleep(t: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count >= iterations:
            raise asyncio.CancelledError()
        await real_sleep(0)

    mocker.patch("pyobs.modules.robotic.mastermind.asyncio.sleep", side_effect=fake_sleep)
    with pytest.raises(asyncio.CancelledError):
        await mm._run_thread()


def _skipped_events(mm: Mastermind) -> list[TaskSkippedEvent]:
    return [c.args[0] for c in mm._comm.send_event.await_args_list if isinstance(c.args[0], TaskSkippedEvent)]


@pytest.mark.asyncio
async def test_run_thread_sends_task_skipped_once_per_stale_window(mocker) -> None:
    mm = make_mastermind()
    _prepare(mm, [make_observation(Task(id=1, name="task1"), duration=1800.0)])

    await _run_briefly(mm, mocker, iterations=8)

    skipped = _skipped_events(mm)
    assert len(skipped) == 1
    assert skipped[0].name == "task1"
    assert skipped[0].id == 1
    assert "start window missed" in skipped[0].reason


@pytest.mark.asyncio
async def test_run_thread_sends_new_task_skipped_for_distinct_stale_window(mocker) -> None:
    mm = make_mastermind()
    _prepare(
        mm,
        [
            make_observation(Task(id=1, name="task1")),
            make_observation(Task(id=2, name="task2")),
        ],
    )

    await _run_briefly(mm, mocker, iterations=10)

    assert [e.id for e in _skipped_events(mm)] == [1, 2]


@pytest.mark.asyncio
async def test_run_thread_does_not_skip_when_task_may_start_late(mocker) -> None:
    mm = make_mastermind()
    mm._vfs = MagicMock()
    mm._vfs.read_yaml = AsyncMock(return_value=None)
    mm._vfs.write_yaml = AsyncMock()
    _prepare(mm, [make_observation(LateStartTask(id=1, name="flats", duration=60.0))])

    await _run_briefly(mm, mocker, iterations=6)

    assert _skipped_events(mm) == []
