from __future__ import annotations

import asyncio
from unittest.mock import patch

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import TimeDelta

from pyobs.robotic import Task
from pyobs.robotic.observation import Observation, ObservationList, ObservationState
from pyobs.robotic.scheduler.constraints import AirmassConstraint
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits import ConstantMerit
from pyobs.robotic.scheduler.ondemandscheduler import OnDemandScheduler
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.robotic.storage.memory import MemoryObservationArchive, MemoryTaskArchive
from pyobs.utils.time import Time
from tests.integration.test_mastermind import NIGHT, FailingRunner, make_mastermind, run_until_state

SAAO = Observer(location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m))


def make_obs_archive() -> MemoryObservationArchive:
    archive = MemoryObservationArchive.__new__(MemoryObservationArchive)
    archive._comm = None
    archive._observer = None
    archive._vfs = None
    archive._timezone = None
    archive._location = None
    archive._observations = ObservationList()
    return archive


def make_task(task_id: int = 1, ra: float = 83.82, dec: float = -5.39, duration: float = 300.0) -> Task:
    return Task(
        id=task_id,
        name=f"task_{task_id}",
        duration=duration,
        target=SiderealTarget(name=f"star_{task_id}", ra=ra, dec=dec),
        merits=[ConstantMerit(merit=1.0)],
    )


async def schedule_tasks(tasks: list[Task], start: Time, end: Time) -> ObservationList:
    """Run the scheduler and return produced observations."""
    scheduler = OnDemandScheduler()
    data = DataProvider(SAAO)
    observations = ObservationList()
    async for obs in scheduler.schedule_in_interval(tasks, {}, start, end, data):
        observations.append(obs)
    return observations


# ── scheduler produces observations ──────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scheduler_produces_observation_for_visible_target() -> None:
    """Scheduler creates an observation for a target that's visible at NIGHT."""
    task = make_task(ra=83.82, dec=-5.39)  # near Orion, visible from SAAO at NIGHT
    end = NIGHT + TimeDelta(3600 * u.second)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        observations = await schedule_tasks([task], NIGHT, end)

    assert len(observations) >= 1
    assert observations[0].task.id == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scheduler_skips_target_failing_airmass() -> None:
    """Scheduler skips a target that fails the airmass constraint."""
    task = Task(
        id=1,
        name="polar",
        duration=300,
        target=SiderealTarget(name="Polaris", ra=37.95, dec=89.26),
        merits=[ConstantMerit(merit=1.0)],
        constraints=[AirmassConstraint(max_airmass=2.0)],
    )
    end = NIGHT + TimeDelta(3600 * u.second)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        observations = await schedule_tasks([task], NIGHT, end)

    assert len(observations) == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scheduler_fills_window_with_multiple_tasks() -> None:
    """Scheduler schedules multiple tasks across a longer window."""
    tasks = [make_task(i, ra=83.82 + i * 10, dec=-5.39) for i in range(1, 4)]
    end = NIGHT + TimeDelta(2 * 3600 * u.second)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        observations = await schedule_tasks(tasks, NIGHT, end)

    assert len(observations) >= 2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scheduler_respects_task_duration() -> None:
    """Scheduled observation end - start matches task duration."""
    task = make_task(duration=600.0, ra=83.82, dec=-5.39)
    end = NIGHT + TimeDelta(3600 * u.second)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        observations = await schedule_tasks([task], NIGHT, end)

    assert len(observations) >= 1
    duration = (observations[0].end - observations[0].start).to(u.second).value
    assert abs(duration - 600.0) < 1.0


# ── scheduler → mastermind pipeline ──────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scheduler_to_mastermind_completes_task() -> None:
    """Full pipeline: scheduler creates observation, mastermind runs it to completion."""
    task = make_task(ra=83.82, dec=-5.39)
    end = NIGHT + TimeDelta(3600 * u.second)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        observations = await schedule_tasks([task], NIGHT, end)

    assert len(observations) >= 1
    obs = observations[0]
    assert obs.state == ObservationState.PENDING

    obs_archive = make_obs_archive()
    await obs_archive.add_observations(ObservationList([obs]))

    mm = make_mastermind(obs_archive)
    reached = await run_until_state(mm, obs_archive, ObservationState.COMPLETED, timeout=30.0)
    assert reached, "Mastermind did not complete the scheduled observation"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scheduler_to_mastermind_failed_task() -> None:
    """Full pipeline: mastermind marks observation FAILED when runner raises."""
    task = make_task(ra=83.82, dec=-5.39)
    end = NIGHT + TimeDelta(3600 * u.second)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        observations = await schedule_tasks([task], NIGHT, end)

    assert len(observations) >= 1

    obs_archive = make_obs_archive()
    await obs_archive.add_observations(ObservationList([observations[0]]))

    mm = make_mastermind(obs_archive, runner=FailingRunner())
    reached = await run_until_state(mm, obs_archive, ObservationState.FAILED, timeout=30.0)
    assert reached, "Mastermind did not mark observation as FAILED"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_memory_task_archive_feeds_scheduler() -> None:
    """MemoryTaskArchive provides tasks to the scheduler correctly."""
    task_archive = MemoryTaskArchive(
        tasks=[
            make_task(1, ra=83.82, dec=-5.39),
            make_task(2, ra=93.82, dec=-5.39),
        ]
    )

    tasks = await task_archive.get_schedulable_tasks()
    assert len(tasks) == 2

    end = NIGHT + TimeDelta(3600 * u.second)
    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        observations = await schedule_tasks(tasks, NIGHT, end)

    assert len(observations) >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scheduler_ignores_future_observation() -> None:
    """Mastermind ignores an observation that hasn't started yet."""
    obs_archive = make_obs_archive()
    future_start = NIGHT + TimeDelta(7200 * u.second)
    future_end = future_start + TimeDelta(300 * u.second)
    obs = Observation(
        task=make_task(),
        start=future_start,
        end=future_end,
        state=ObservationState.PENDING,
    )
    await obs_archive.add_observations(ObservationList([obs]))

    mm = make_mastermind(obs_archive)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        task_handle = asyncio.create_task(mm._run_thread())
        await asyncio.sleep(0.3)
        mm._running = False
        task_handle.cancel()
        try:
            await task_handle
        except (asyncio.CancelledError, Exception):
            pass

    assert mm._task is None
