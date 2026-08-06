from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.robotic import Observation, Task
from pyobs.robotic.observation import ObservationList
from pyobs.robotic.scheduler.observationarchiveevolution import ObservationArchiveEvolution
from pyobs.utils.time import Time


def make_observer() -> Observer:
    return Observer(location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m))


def make_task(task_id: int = 1) -> Task:
    return Task(id=task_id, name=f"task_{task_id}", duration=100)


# ── prefetch + freeze with mock archive ──────────────────────────────────────


@pytest.mark.asyncio
async def test_prefetch_populates_task_and_night_cache() -> None:
    mock_archive = MagicMock()
    mock_archive.get_observations = AsyncMock(side_effect=lambda **kwargs: ObservationList())

    observer = make_observer()
    evolution = ObservationArchiveEvolution(observer, mock_archive)
    tasks = [make_task(1), make_task(2)]
    start = Time.now()
    night = start.to_datetime().date()

    await evolution.prefetch(tasks, start, night)

    assert mock_archive.get_observations.call_count == 3  # 2 tasks + 1 night
    assert not evolution._frozen


@pytest.mark.asyncio
async def test_freeze_prevents_lazy_task_fetch() -> None:
    mock_archive = MagicMock()
    mock_archive.get_observations = AsyncMock(side_effect=lambda **kwargs: ObservationList())

    observer = make_observer()
    evolution = ObservationArchiveEvolution(observer, mock_archive)
    tasks = [make_task(1)]
    start = Time.now()
    night = start.to_datetime().date()

    await evolution.prefetch(tasks, start, night)
    evolution.freeze()

    # Task 1 was prefetched -- should return cached
    obs = await evolution.observations_for_task(make_task(1))
    assert obs is not None

    # Task 2 was NOT prefetched -- should raise
    with pytest.raises(RuntimeError, match="not in observation cache after freeze"):
        await evolution.observations_for_task(make_task(2))

    # Archive should never be called after freeze
    assert mock_archive.get_observations.call_count == 2  # 1 task + 1 night from prefetch


@pytest.mark.asyncio
async def test_freeze_night_miss_seeds_empty() -> None:
    mock_archive = MagicMock()
    mock_archive.get_observations = AsyncMock(side_effect=lambda **kwargs: ObservationList())

    observer = make_observer()
    evolution = ObservationArchiveEvolution(observer, mock_archive)
    tasks = [make_task(1)]
    start = Time.now()
    night = start.to_datetime().date()

    await evolution.prefetch(tasks, start, night)
    evolution.freeze()

    # Current night (prefetched) returns cached data
    obs = await evolution.observations_for_night(night)
    assert obs is not None
    assert mock_archive.get_observations.call_count == 2

    # Future night (not prefetched) seeds empty, no archive call
    future_night = night + datetime.timedelta(days=1)
    obs = await evolution.observations_for_night(future_night)
    assert len(obs) == 0
    assert mock_archive.get_observations.call_count == 2  # still 2, no new calls


@pytest.mark.asyncio
async def test_evolve_after_freeze_prefetched_task() -> None:
    mock_archive = MagicMock()
    mock_archive.get_observations = AsyncMock(side_effect=lambda **kwargs: ObservationList())

    observer = make_observer()
    evolution = ObservationArchiveEvolution(observer, mock_archive)
    task = make_task(1)
    tasks = [task]
    start = Time.now()
    night = start.to_datetime().date()

    await evolution.prefetch(tasks, start, night)
    evolution.freeze()

    scheduled = Observation(task=task, start=start, end=start, priority=1.0)
    await evolution.evolve(scheduled, night)

    assert len(evolution._obs_for_task[task.id]) == 1
    assert len(evolution._obs_for_night[night]) == 1
    assert mock_archive.get_observations.call_count == 2


@pytest.mark.asyncio
async def test_evolve_after_freeze_future_night() -> None:
    mock_archive = MagicMock()
    mock_archive.get_observations = AsyncMock(side_effect=lambda **kwargs: ObservationList())

    observer = make_observer()
    evolution = ObservationArchiveEvolution(observer, mock_archive)
    task = make_task(1)
    tasks = [task]
    start = Time.now()
    night = start.to_datetime().date()

    await evolution.prefetch(tasks, start, night)
    evolution.freeze()

    future_night = night + datetime.timedelta(days=1)
    scheduled = Observation(task=task, start=start, end=start, priority=1.0)
    await evolution.evolve(scheduled, future_night)

    assert len(evolution._obs_for_task[task.id]) == 1
    assert len(evolution._obs_for_night[future_night]) == 1
    assert mock_archive.get_observations.call_count == 2


# ── prefetch + freeze without archive (None) ─────────────────────────────────


@pytest.mark.asyncio
async def test_prefetch_without_archive() -> None:
    observer = make_observer()
    evolution = ObservationArchiveEvolution(observer, None)
    tasks = [make_task(1), make_task(2)]
    start = Time.now()
    night = start.to_datetime().date()

    await evolution.prefetch(tasks, start, night)
    evolution.freeze()

    assert len(evolution._obs_for_task) == 2
    assert len(evolution._obs_for_night) == 1


@pytest.mark.asyncio
async def test_freeze_without_archive_unprefetched_task_raises() -> None:
    observer = make_observer()
    evolution = ObservationArchiveEvolution(observer, None)
    tasks = [make_task(1)]
    start = Time.now()
    night = start.to_datetime().date()

    await evolution.prefetch(tasks, start, night)
    evolution.freeze()

    with pytest.raises(RuntimeError, match="not in observation cache after freeze"):
        await evolution.observations_for_task(make_task(99))


# ── freeze canary assertion ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_freeze_night_canary_catches_past_night() -> None:
    mock_archive = MagicMock()
    mock_archive.get_observations = AsyncMock(side_effect=lambda **kwargs: ObservationList())

    observer = make_observer()
    evolution = ObservationArchiveEvolution(observer, mock_archive)
    tasks = [make_task(1)]
    start = Time.now()
    night = start.to_datetime().date()

    await evolution.prefetch(tasks, start, night)
    evolution.freeze()

    # Asking for a *previous* night (should never happen in normal scheduling)
    # triggers the canary assertion
    past_night = night - datetime.timedelta(days=1)
    with pytest.raises(AssertionError):
        await evolution.observations_for_night(past_night)
