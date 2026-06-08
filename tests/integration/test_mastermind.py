from __future__ import annotations

import asyncio
import os
from unittest.mock import patch

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import TimeDelta
from filelock import FileLock

from pyobs.comm.dummy.dummycomm import DummyComm
from pyobs.modules.robotic.mastermind import Mastermind
from pyobs.robotic import Task
from pyobs.robotic.filesystem.observationarchive import YamlObservationArchive
from pyobs.robotic.observation import Observation, ObservationList, ObservationState
from pyobs.robotic.taskrunner import TaskRunner
from pyobs.utils.time import Time

# ── module-level script stubs ─────────────────────────────────────────────────


class QuickRunner(TaskRunner):
    """TaskRunner that immediately completes any task."""

    def __new__(cls):
        obj = object.__new__(cls)
        obj._comm = None
        obj._observer = None
        obj._vfs = None
        obj._timezone = None
        obj._location = None
        obj.observation_archive = None
        obj.task_archive = None
        return obj

    async def can_run(self, task) -> bool:
        return True

    async def run_task(self, task) -> bool:
        await asyncio.sleep(0.05)
        return True


class FailingRunner(TaskRunner):
    """TaskRunner that always raises."""

    def __new__(cls):
        obj = object.__new__(cls)
        obj._comm = None
        obj._observer = None
        obj._vfs = None
        obj._timezone = None
        obj._location = None
        obj.observation_archive = None
        obj.task_archive = None
        return obj

    async def can_run(self, task) -> bool:
        return True

    async def run_task(self, task) -> bool:
        raise RuntimeError("intentional failure")


# ── helpers ───────────────────────────────────────────────────────────────────

SAAO = Observer(location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m))

# Fixed night time at SAAO — used for both writing and querying observations
NIGHT = Time("2025-11-03T23:00:00", scale="utc")


def make_obs_archive(tmp_path) -> YamlObservationArchive:
    archive = YamlObservationArchive.__new__(YamlObservationArchive)
    archive._comm = None
    archive._vfs = None
    archive._timezone = None
    archive._location = None
    archive._observer = SAAO
    archive._path = str(tmp_path)
    archive._extension = "yaml"
    archive._mode = "night"
    archive._lock = FileLock(os.path.join(str(tmp_path), ".lock"))
    return archive


def make_mastermind(obs_archive, runner=None) -> Mastermind:
    if runner is None:
        runner = QuickRunner()
    runner.observation_archive = obs_archive

    mm = Mastermind.__new__(Mastermind)
    mm._comm = DummyComm()
    mm._observer = None
    mm._vfs = None
    mm._timezone = None
    mm._location = None
    mm._allowed_late_start = 300
    mm._allowed_overrun = 300
    mm._after_task_sleep = 0
    mm._running = True
    mm._task = None
    mm._task_archive = None
    mm._observation_archive = obs_archive
    mm._task_runner = runner
    return mm


def make_obs(duration: float = 60.0) -> Observation:
    task = Task(id=1, name="test_task", duration=duration)
    return Observation(
        task=task,
        start=NIGHT - TimeDelta(10 * u.second),
        end=NIGHT + TimeDelta(duration * u.second),
        state=ObservationState.PENDING,
    )


async def run_until_state(
    mm: Mastermind,
    obs_archive: YamlObservationArchive,
    target_state: ObservationState,
    timeout: float = 10.0,
) -> bool:
    """Run mastermind _run_thread until the observation reaches target_state.

    Patches Time.now() to return NIGHT so the archive loads the correct file.
    """
    reached = asyncio.Event()
    original_update = obs_archive.update_observation

    async def tracking_update(o):
        await original_update(o)
        if o.state == target_state:
            reached.set()

    obs_archive.update_observation = tracking_update

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        task_handle = asyncio.create_task(mm._run_thread())
        try:
            await asyncio.wait_for(reached.wait(), timeout=timeout)
            return True
        except TimeoutError:
            return False
        finally:
            mm._running = False
            task_handle.cancel()
            try:
                await task_handle
            except (asyncio.CancelledError, Exception):
                pass
            obs_archive.update_observation = original_update


# ── tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_runs_task_to_completion(tmp_path) -> None:
    """Mastermind picks up a pending observation and runs it to COMPLETED."""
    obs_archive = make_obs_archive(tmp_path)
    mm = make_mastermind(obs_archive)
    await obs_archive.add_observations(ObservationList([make_obs()]))

    reached = await run_until_state(mm, obs_archive, ObservationState.COMPLETED)

    assert reached, "Observation did not reach COMPLETED state within timeout"
    loaded = await obs_archive.get_schedule(NIGHT)
    assert any(o.state == ObservationState.COMPLETED for o in loaded)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_marks_failed_on_exception(tmp_path) -> None:
    """Mastermind marks observation FAILED when script raises."""
    obs_archive = make_obs_archive(tmp_path)
    mm = make_mastermind(obs_archive, runner=FailingRunner())
    await obs_archive.add_observations(ObservationList([make_obs()]))

    reached = await run_until_state(mm, obs_archive, ObservationState.FAILED)

    assert reached, "Observation did not reach FAILED state within timeout"
    loaded = await obs_archive.get_schedule(NIGHT)
    assert any(o.state == ObservationState.FAILED for o in loaded)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_sends_task_started_event(tmp_path) -> None:
    """Mastermind sends TaskStartedEvent when a task begins."""
    from pyobs.events import TaskStartedEvent

    obs_archive = make_obs_archive(tmp_path)
    mm = make_mastermind(obs_archive)
    await obs_archive.add_observations(ObservationList([make_obs()]))

    events_sent = []
    original_send = mm._comm.send_event

    async def tracking_send(event):
        events_sent.append(event)
        return await original_send(event)

    mm._comm.send_event = tracking_send

    await run_until_state(mm, obs_archive, ObservationState.COMPLETED)

    task_started = [e for e in events_sent if isinstance(e, TaskStartedEvent)]
    assert len(task_started) == 1
    assert task_started[0].name == "test_task"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_skips_when_no_observation(tmp_path) -> None:
    """Mastermind does nothing when archive is empty — _task stays None."""
    obs_archive = make_obs_archive(tmp_path)
    mm = make_mastermind(obs_archive)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        task_handle = asyncio.create_task(mm._run_thread())
        await asyncio.sleep(0.5)
        mm._running = False
        task_handle.cancel()
        try:
            await task_handle
        except (asyncio.CancelledError, Exception):
            pass

    assert mm._task is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_marks_observation_in_progress(tmp_path) -> None:
    """Mastermind sets observation to IN_PROGRESS before running the task."""
    obs_archive = make_obs_archive(tmp_path)
    mm = make_mastermind(obs_archive)
    await obs_archive.add_observations(ObservationList([make_obs()]))

    reached = await run_until_state(mm, obs_archive, ObservationState.IN_PROGRESS)
    assert reached, "Observation did not reach IN_PROGRESS state"
