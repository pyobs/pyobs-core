from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import patch

import astropy.units as u
import pytest
from astropy.time import TimeDelta

from pyobs.modules.robotic.mastermind import Mastermind
from pyobs.robotic import Task
from pyobs.robotic.observation import Observation, ObservationList, ObservationState
from pyobs.robotic.storage.memory import MemoryObservationArchive
from pyobs.robotic.taskrunner import TaskRunner
from pyobs.utils.time import Time

# ── runner stubs ──────────────────────────────────────────────────────────────


class QuickRunner(TaskRunner):
    """TaskRunner that immediately completes any task."""

    async def can_run(self, task, target=None) -> bool:
        return True

    async def run_task(self, task, target=None) -> bool:
        await asyncio.sleep(0.05)
        return True


class FailingRunner(TaskRunner):
    """TaskRunner that always raises."""

    async def can_run(self, task, target=None) -> bool:
        return True

    async def run_task(self, task, target=None) -> bool:
        raise RuntimeError("intentional failure")


# ── fixed time so get_next_observation finds our observations ─────────────────

NIGHT = Time("2025-11-03T23:00:00", scale="utc")


# ── helpers ───────────────────────────────────────────────────────────────────


def make_obs_archive() -> MemoryObservationArchive:
    return MemoryObservationArchive()


def make_mastermind(obs_archive, runner=None, task_archive=None) -> Mastermind:
    if runner is None:
        runner = QuickRunner()
    runner.observation_archive = obs_archive

    # in-memory vfs so the obsnum cache file never touches real disk
    mm = Mastermind(
        schedule=obs_archive,
        runner=runner,
        tasks=task_archive,
        vfs={
            "class": "pyobs.vfs.VirtualFileSystem",
            "roots": {"pyobs": {"class": "pyobs.vfs.MemoryFile"}},
        },
    )
    mm._running = True  # skip open()/start(), which would also register comm event handlers
    return mm


def make_obs(duration: float = 60.0, obs_id: Any = None) -> Observation:
    task = Task(id=1, name="test_task", duration=duration)
    return Observation(
        id=obs_id,
        task=task,
        start=NIGHT - TimeDelta(10 * u.second),
        end=NIGHT + TimeDelta(duration * u.second),
        state=ObservationState.PENDING,
    )


async def run_until_state(
    mm: Mastermind,
    obs_archive: MemoryObservationArchive,
    target_state: ObservationState,
    timeout: float = 10.0,
    now: Time | None = None,
) -> bool:
    """Run mastermind _run_thread until the observation reaches target_state.

    Args:
        now: Time to patch Time.now() with. Defaults to NIGHT.
    """
    if now is None:
        now = NIGHT
    reached = asyncio.Event()
    original_update = obs_archive.update_observation

    async def tracking_update(o):
        await original_update(o)
        if o.state == target_state:
            reached.set()

    obs_archive.update_observation = tracking_update

    with patch("pyobs.utils.time.Time.now", return_value=now):
        task_handle = asyncio.create_task(mm._run_thread())
        try:
            await asyncio.wait_for(reached.wait(), timeout=timeout)
            return True
        except TimeoutError:
            return False
        finally:
            await mm.stop()
            task_handle.cancel()
            try:
                await task_handle
            except (asyncio.CancelledError, Exception):
                pass
            obs_archive.update_observation = original_update


@pytest.fixture(autouse=True)
def _clear_vfs_buffer():
    """MemoryFile's buffer is a process-wide class dict; every Mastermind instance in these
    tests shares the same (unnamed) module path, so it must be reset between tests."""
    from pyobs.vfs.bufferedfile import BufferedFile

    BufferedFile._bufferedFiles.clear()
    yield
    BufferedFile._bufferedFiles.clear()


# ── tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_runs_task_to_completion() -> None:
    """Mastermind picks up a pending observation and runs it to COMPLETED."""
    obs_archive = make_obs_archive()
    mm = make_mastermind(obs_archive)
    await obs_archive.add_observations(ObservationList([make_obs()]))

    reached = await run_until_state(mm, obs_archive, ObservationState.COMPLETED)

    assert reached, "Observation did not reach COMPLETED state within timeout"
    loaded = await obs_archive.get_schedule()
    assert any(o.state == ObservationState.COMPLETED for o in loaded)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_marks_failed_on_exception() -> None:
    """Mastermind marks observation FAILED when script raises."""
    obs_archive = make_obs_archive()
    mm = make_mastermind(obs_archive, runner=FailingRunner())
    await obs_archive.add_observations(ObservationList([make_obs()]))

    reached = await run_until_state(mm, obs_archive, ObservationState.FAILED)

    assert reached, "Observation did not reach FAILED state within timeout"
    loaded = await obs_archive.get_schedule()
    assert any(o.state == ObservationState.FAILED for o in loaded)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_sends_task_started_event() -> None:
    """Mastermind sends TaskStartedEvent when a task begins."""
    from pyobs.events import TaskStartedEvent

    obs_archive = make_obs_archive()
    mm = make_mastermind(obs_archive)
    await obs_archive.add_observations(ObservationList([make_obs()]))

    events_sent = []
    original_send = mm.comm.send_event

    async def tracking_send(event):
        events_sent.append(event)
        return await original_send(event)

    mm.comm.send_event = tracking_send

    await run_until_state(mm, obs_archive, ObservationState.COMPLETED)

    task_started = [e for e in events_sent if isinstance(e, TaskStartedEvent)]
    assert len(task_started) == 1
    assert task_started[0].name == "test_task"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_skips_when_no_observation() -> None:
    """Mastermind does nothing when archive is empty — _task stays None."""
    obs_archive = make_obs_archive()
    mm = make_mastermind(obs_archive)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        task_handle = asyncio.create_task(mm._run_thread())
        await asyncio.sleep(0.5)
        await mm.stop()
        task_handle.cancel()
        try:
            await task_handle
        except (asyncio.CancelledError, Exception):
            pass

    assert mm._task is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_marks_observation_in_progress() -> None:
    """Mastermind sets observation to IN_PROGRESS before running the task."""
    obs_archive = make_obs_archive()
    mm = make_mastermind(obs_archive)
    await obs_archive.add_observations(ObservationList([make_obs()]))

    reached = await run_until_state(mm, obs_archive, ObservationState.IN_PROGRESS)
    assert reached, "Observation did not reach IN_PROGRESS state"


# ── obsnum tests ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_assigns_obsnum_to_observation() -> None:
    """Observation.obsnum is set to "<night>-001" for the first observation of a night."""
    obs_archive = make_obs_archive()
    mm = make_mastermind(obs_archive)
    await obs_archive.add_observations(ObservationList([make_obs()]))

    await run_until_state(mm, obs_archive, ObservationState.COMPLETED)

    loaded = await obs_archive.get_schedule()
    assert any(o.obsnum == "20251103-001" for o in loaded)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_reports_obsnum_in_fits_header() -> None:
    """OBSNUM appears in get_fits_header_before() with the same value as Observation.obsnum."""
    obs_archive = make_obs_archive()
    mm = make_mastermind(obs_archive)
    await obs_archive.add_observations(ObservationList([make_obs(duration=1.0)]))

    seen_headers = []
    original_update = obs_archive.update_observation

    async def tracking_update(o):
        seen_headers.append(await mm.get_fits_header_before())
        await original_update(o)

    obs_archive.update_observation = tracking_update

    await run_until_state(mm, obs_archive, ObservationState.IN_PROGRESS)
    obs_archive.update_observation = original_update

    # header was requested after obsnum was assigned but before update_observation ran
    assert any("OBSNUM" in h for h in seen_headers)
    header_obsnum = next(h["OBSNUM"].value for h in seen_headers if "OBSNUM" in h)
    assert header_obsnum == "20251103-001"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_increments_obsnum_within_a_night() -> None:
    """Two observations run back-to-back on the same night get consecutive obsnums."""
    obs_archive = make_obs_archive()
    mm = make_mastermind(obs_archive)
    await obs_archive.add_observations(ObservationList([make_obs(duration=1.0, obs_id=1)]))
    await run_until_state(mm, obs_archive, ObservationState.COMPLETED)

    await obs_archive.add_observations(ObservationList([make_obs(duration=1.0, obs_id=2)]))
    mm._running = True  # run_until_state's finally block stopped it after the first run
    await run_until_state(mm, obs_archive, ObservationState.COMPLETED)

    obsnums = sorted(o.obsnum for o in await obs_archive.get_schedule() if o.obsnum is not None)
    assert obsnums == ["20251103-001", "20251103-002"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_resets_obsnum_on_new_night() -> None:
    """obsnum resets to 001 when the night changes."""
    obs_archive = make_obs_archive()
    mm = make_mastermind(obs_archive)
    await obs_archive.add_observations(ObservationList([make_obs(duration=1.0, obs_id=1)]))
    await run_until_state(mm, obs_archive, ObservationState.COMPLETED)

    next_night = NIGHT + TimeDelta(1 * u.day)
    obs = make_obs(duration=1.0, obs_id=2)
    obs.start = next_night - TimeDelta(10 * u.second)
    obs.end = next_night + TimeDelta(1.0 * u.second)
    await obs_archive.add_observations(ObservationList([obs]))
    mm._running = True  # run_until_state's finally block stopped it after the first run
    await run_until_state(mm, obs_archive, ObservationState.COMPLETED, now=next_night)

    obsnums = {o.start.strftime("%Y%m%d"): o.obsnum for o in await obs_archive.get_schedule()}
    assert obsnums[NIGHT.strftime("%Y%m%d")] == "20251103-001"
    assert obsnums[next_night.strftime("%Y%m%d")] == "20251104-001"
