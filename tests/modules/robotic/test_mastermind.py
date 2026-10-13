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
from pyobs.robotic.scheduler.constraints import (
    AirmassConstraint,
    MoonIlluminationConstraint,
    MoonSeparationConstraint,
    SolarElevationConstraint,
    TimeConstraint,
)
from pyobs.robotic.scheduler.constraints.constraint import Constraint
from pyobs.robotic.task import Project, Task
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


# ── REQ cards: what the frame was asked for (#962) ───────────────────────────


def make_request_task(**kwargs) -> Task:
    return Task(id=1, name="task1", project="p1", **kwargs)


@pytest.mark.asyncio
async def test_header_has_priority_and_all_constraint_cards(mocker) -> None:
    mocker.patch("pyobs.modules.robotic.mastermind.version_fits_headers", return_value={})
    mm = make_mastermind()
    start = Time("2026-10-13T20:00:00")
    mm._task = make_request_task(
        priority=2.5,
        constraints=[
            AirmassConstraint(max_airmass=1.4),
            MoonSeparationConstraint(min_distance=20.0),
            MoonIlluminationConstraint(max_phase=0.5),
            SolarElevationConstraint(),
            TimeConstraint(start=start, end=start + 1.0 * u.hour),
        ],
    )
    mm._project_priority = 3.0

    hdr = await mm.get_fits_header_before()

    assert {k: v.value for k, v in hdr.items() if k.startswith("HIERARCH REQ")} == {
        "HIERARCH REQ PRIORITY": 2.5,
        "HIERARCH REQ PROJECT PRIORITY": 3.0,
        "HIERARCH REQ AIRMASS MAX": 1.4,
        "HIERARCH REQ MOONDIST MIN": 20.0,
        "HIERARCH REQ MOONFRAC MAX": 0.5,
        "HIERARCH REQ SUNALT MIN": -90.0,
        "HIERARCH REQ SUNALT MAX": -18.0,
        "HIERARCH REQ SUNALT DIR": "both",
        "HIERARCH REQ TIME START": "2026-10-13T20:00:00.000",
        "HIERARCH REQ TIME END": "2026-10-13T21:00:00.000",
    }
    assert hdr["REQNUM"].value == "1"


@pytest.mark.asyncio
async def test_header_numbers_constraints_of_the_same_type(mocker) -> None:
    mocker.patch("pyobs.modules.robotic.mastermind.version_fits_headers", return_value={})
    mm = make_mastermind()
    start = Time("2026-10-13T20:00:00")
    mm._task = make_request_task(
        constraints=[
            SolarElevationConstraint(max_elevation=-12.0),
            SolarElevationConstraint(max_elevation=-18.0),
            TimeConstraint(start=start, end=start + 1.0 * u.hour),
            TimeConstraint(start=start + 2.0 * u.hour, end=start + 3.0 * u.hour),
        ]
    )

    hdr = await mm.get_fits_header_before()

    assert hdr["HIERARCH REQ SUNALT MAX"].value == -12.0
    assert hdr["HIERARCH REQ SUNALT2 MAX"].value == -18.0
    assert hdr["HIERARCH REQ TIME START"].value == "2026-10-13T20:00:00.000"
    assert hdr["HIERARCH REQ TIME2 START"].value == "2026-10-13T22:00:00.000"


@pytest.mark.asyncio
async def test_header_without_constraints_and_priority_has_no_req_cards(mocker) -> None:
    mocker.patch("pyobs.modules.robotic.mastermind.version_fits_headers", return_value={})
    mm = make_mastermind()
    mm._task = make_request_task(priority=None)

    hdr = await mm.get_fits_header_before()

    assert not [k for k in hdr if k.startswith("HIERARCH REQ")]
    assert hdr["TASK"].value == "task1"


@pytest.mark.asyncio
async def test_header_plugin_constraint_adds_nothing(mocker) -> None:
    class PluginConstraint(Constraint):
        def to_astroplan(self):
            raise NotImplementedError

        async def __call__(self, time, task, data) -> bool:
            return True

    mocker.patch("pyobs.modules.robotic.mastermind.version_fits_headers", return_value={})
    mm = make_mastermind()
    mm._task = make_request_task(priority=None, constraints=[PluginConstraint()])

    hdr = await mm.get_fits_header_before()

    assert not [k for k in hdr if k.startswith("HIERARCH REQ")]


@pytest.mark.asyncio
async def test_header_keeps_first_card_on_a_key_clash(mocker) -> None:
    class StrictAirmass(AirmassConstraint):
        pass

    mocker.patch("pyobs.modules.robotic.mastermind.version_fits_headers", return_value={})
    mm = make_mastermind()
    mm._task = make_request_task(
        priority=None, constraints=[AirmassConstraint(max_airmass=1.3), StrictAirmass(max_airmass=1.1)]
    )

    hdr = await mm.get_fits_header_before()

    assert hdr["HIERARCH REQ AIRMASS MAX"].value == 1.3


@pytest.mark.asyncio
async def test_lookup_project_priority() -> None:
    mm = make_mastermind()
    task = make_request_task()

    # no task archive
    mm._task_archive = None
    assert await mm._lookup_project_priority(task) is None

    # archive with the project
    mm._task_archive = MagicMock()
    mm._task_archive.get_projects = AsyncMock(return_value=[Project(code="x"), Project(code="p1", priority=4.0)])
    assert await mm._lookup_project_priority(task) == 4.0

    # unknown project, project without priority, task without project
    assert await mm._lookup_project_priority(Task(id=2, name="t", project="other")) is None
    mm._task_archive.get_projects = AsyncMock(return_value=[Project(code="p1", priority=None)])
    assert await mm._lookup_project_priority(task) is None
    assert await mm._lookup_project_priority(Task(id=3, name="t")) is None

    # archive without projects (e.g. filesystem)
    mm._task_archive.get_projects = AsyncMock(side_effect=NotImplementedError)
    assert await mm._lookup_project_priority(task) is None


@pytest.mark.asyncio
async def test_project_priority_is_taken_at_task_start_and_cleared_afterwards(mocker) -> None:
    mocker.patch("pyobs.modules.robotic.mastermind.version_fits_headers", return_value={})
    mm = make_mastermind()
    project = Project(code="p1", priority=4.0)
    mm._task_archive = MagicMock()
    mm._task_archive.get_projects = AsyncMock(return_value=[project])
    _prepare(mm, [make_observation(make_request_task(), start=Time.now())])
    mm._next_obsnum = AsyncMock(return_value="20261013-001")

    seen: list[object] = []

    async def run_task(task: Task, target: object) -> None:
        # the project changes while the task runs: the frames of this run keep the value from the start
        project.priority = 9.0
        hdr = await mm.get_fits_header_before()
        seen.append(hdr["HIERARCH REQ PROJECT PRIORITY"].value)

    mm._task_runner.run_task = run_task

    await _run_briefly(mm, mocker, iterations=2)  # cancelled in the sleep after the first task

    assert seen == [4.0]
    assert mm._project_priority is None


@pytest.mark.asyncio
async def test_project_priority_is_cleared_after_a_failed_task(mocker) -> None:
    mm = make_mastermind()
    mm._task_archive = MagicMock()
    mm._task_archive.get_projects = AsyncMock(return_value=[Project(code="p1", priority=4.0)])
    _prepare(mm, [make_observation(make_request_task(), start=Time.now())])
    mm._next_obsnum = AsyncMock(return_value="20261013-001")
    mm._task_runner.run_task = AsyncMock(side_effect=RuntimeError("failed"))
    # a failed task loops straight on without sleeping: end the loop with the second lookup
    mm._observation_archive.get_next_observation = AsyncMock(
        side_effect=[make_observation(make_request_task(), start=Time.now()), asyncio.CancelledError()]
    )

    await _run_briefly(mm, mocker)

    assert mm._project_priority is None
    assert mm._task is None


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
