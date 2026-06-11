from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import astropy.units as u
import pytest
from astropy.time import TimeDelta

from pyobs.robotic.observation import Observation, ObservationList, ObservationState
from pyobs.robotic.storage.lco._portal import Portal
from pyobs.robotic.storage.lco._schedulereader import LcoScheduleReader
from pyobs.utils.time import Time

from .helpers import make_portal

T0 = Time("2026-06-03T21:25:00", scale="utc")
T1 = Time("2026-06-03T21:28:00", scale="utc")


def make_reader(portal: Portal | None = None, auto_updates: bool = False) -> LcoScheduleReader:
    reader = LcoScheduleReader.__new__(LcoScheduleReader)
    reader._comm = None
    reader._observer = None
    reader._vfs = None
    reader._timezone = None
    reader._location = None
    reader._portal = portal or make_portal()
    reader._site = "goe"
    reader._telescope = "0m5a"
    reader._last_schedule_time = None
    reader._update_lock = asyncio.Lock()
    reader._auto_updates = auto_updates
    reader._last_scheduled = None
    reader._scheduled_tasks = ObservationList()
    reader._update_error_log = MagicMock()
    reader._update_error_log.resolve = MagicMock()
    reader._update_error_log.error = MagicMock()
    return reader


def make_observation(start: Time = T0, end: Time = T1) -> Observation:
    from pyobs.robotic.storage.lco.task import LcoTask

    from .conftest import OBSERVATIONS_RESPONSE

    obs_data = OBSERVATIONS_RESPONSE["results"][0]
    task = LcoTask.from_observation(
        MagicMock(start=start, end=end, request=MagicMock(id=obs_data["request"]["id"], configurations=[])), {}
    )
    return Observation(task=task, start=start, end=end, state=ObservationState.PENDING)


# ── get_schedule ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_schedule_returns_empty_initially() -> None:
    reader = make_reader()
    result = await reader.get_schedule()
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_schedule_returns_cached_tasks() -> None:
    reader = make_reader()
    obs = Observation(task=MagicMock(id=1, name="t"), start=T0, end=T1)
    reader._scheduled_tasks = ObservationList([obs])
    result = await reader.get_schedule()
    assert len(result) == 1


# ── get_task ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_task_returns_active_observation() -> None:
    reader = make_reader()
    reader._update_schedule_now = AsyncMock()

    obs = MagicMock()
    obs.start = T0 - TimeDelta(60 * u.second)
    obs.end = T1 + TimeDelta(60 * u.second)
    obs.task.is_finished.return_value = False

    reader._scheduled_tasks = ObservationList([obs])
    mid = T0 + TimeDelta(30 * u.second)

    result = await reader.get_task(mid)
    assert result is obs


@pytest.mark.asyncio
async def test_get_task_returns_none_before_window() -> None:
    reader = make_reader()
    reader._update_schedule_now = AsyncMock()

    obs = MagicMock()
    obs.start = T1
    obs.end = T1 + TimeDelta(300 * u.second)
    obs.task.is_finished.return_value = False

    reader._scheduled_tasks = ObservationList([obs])
    result = await reader.get_task(T0)
    assert result is None


@pytest.mark.asyncio
async def test_get_task_skips_finished_tasks() -> None:
    reader = make_reader()
    reader._update_schedule_now = AsyncMock()

    obs = MagicMock()
    obs.start = T0 - TimeDelta(60 * u.second)
    obs.end = T1 + TimeDelta(60 * u.second)
    obs.task.is_finished.return_value = True

    reader._scheduled_tasks = ObservationList([obs])
    result = await reader.get_task(T0)
    assert result is None


@pytest.mark.asyncio
async def test_get_task_calls_update_schedule_now() -> None:
    reader = make_reader()
    reader._update_schedule_now = AsyncMock()
    reader._scheduled_tasks = ObservationList()

    await reader.get_task(T0)
    reader._update_schedule_now.assert_called_once()


# ── _download_schedule ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_download_schedule_returns_observations(mocker) -> None:
    from pyobs.robotic.storage.lco._portal import LcoObservation

    from .conftest import OBSERVATIONS_RESPONSE

    reader = make_reader()
    obs = LcoObservation(**OBSERVATIONS_RESPONSE["results"][0])
    mocker.patch.object(reader._portal, "download_schedule", AsyncMock(return_value=[obs]))

    result = await reader._download_schedule(start_before=T1, end_after=T0)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_download_schedule_empty_portal_response(mocker) -> None:
    reader = make_reader()
    mocker.patch.object(reader._portal, "download_schedule", AsyncMock(return_value=[]))
    result = await reader._download_schedule(start_before=T1, end_after=T0)
    assert len(result) == 0


# ── _update_schedule_now ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_schedule_now_updates_cache(mocker) -> None:
    reader = make_reader()
    now = Time.now()
    obs = MagicMock()
    obs.start = now
    obs.end = now + TimeDelta(300 * u.second)

    mocker.patch.object(reader, "_download_schedule", AsyncMock(return_value=ObservationList([obs])))

    await reader._update_schedule_now()
    assert len(reader._scheduled_tasks) == 1


@pytest.mark.asyncio
async def test_update_schedule_now_sets_last_schedule_time(mocker) -> None:
    reader = make_reader()
    assert reader._last_schedule_time is None

    mocker.patch.object(reader, "_download_schedule", AsyncMock(return_value=ObservationList([MagicMock()])))

    await reader._update_schedule_now()
    assert reader._last_schedule_time is not None


@pytest.mark.asyncio
async def test_update_schedule_now_respects_lock(mocker) -> None:
    """Does not update if lock cannot be acquired within timeout."""
    from pyobs.utils.parallel import acquire_lock as real_acquire_lock

    reader = make_reader()
    await reader._update_lock.acquire()  # hold the lock

    download_mock = mocker.patch.object(reader, "_download_schedule", AsyncMock(return_value=ObservationList()))

    # use real acquire_lock but with 0.01s timeout instead of 20s
    async def fast_acquire(lock, timeout):
        return await real_acquire_lock(lock, 0.01)

    with patch("pyobs.robotic.storage.lco._schedulereader.acquire_lock", fast_acquire):
        await reader._update_schedule_now()

    download_mock.assert_not_called()
    reader._update_lock.release()
