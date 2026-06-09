from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import astropy.units as u
import pytest
from astropy.time import TimeDelta

from pyobs.robotic import Task
from pyobs.robotic.observation import Observation, ObservationList, ObservationState
from pyobs.robotic.storage.backend.observationarchive import BackendObservationArchive
from pyobs.robotic.storage.backend.taskarchive import BackendTaskArchive
from pyobs.robotic.task import Project
from pyobs.utils.time import Time

# ── fixtures ──────────────────────────────────────────────────────────────────

T0 = Time("2025-11-03T23:00:00", scale="utc")
T1 = T0 + TimeDelta(300 * u.second)
T2 = T1 + TimeDelta(300 * u.second)


def make_task(task_id: int = 1) -> Task:
    return Task(id=task_id, name=f"task_{task_id}", duration=300)


def make_obs(
    task: Task, start: Time = T0, end: Time = T1, state: ObservationState = ObservationState.PENDING
) -> Observation:
    return Observation(task=task, start=start, end=end, state=state)


def make_task_archive() -> BackendTaskArchive:
    archive = BackendTaskArchive.__new__(BackendTaskArchive)
    archive._comm = None
    archive._observer = None
    archive._vfs = None
    archive._timezone = None
    archive._location = None
    archive._url = "http://localhost:8000"
    archive._token = "testtoken"
    archive._aiohttp_session = MagicMock()
    archive._last_update = None
    archive._projects = []
    archive._tasks = []
    archive._on_tasks_changed = None
    return archive


def make_obs_archive() -> BackendObservationArchive:
    archive = BackendObservationArchive.__new__(BackendObservationArchive)
    archive._comm = None
    archive._observer = None
    archive._vfs = None
    archive._timezone = None
    archive._location = None
    archive._url = "http://localhost:8000"
    archive._token = "testtoken"
    archive._aiohttp_session = MagicMock()
    archive._last_update = None
    archive._observations = ObservationList()
    return archive


# ── BackendTaskArchive ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_task_last_changed_none_initially() -> None:
    archive = make_task_archive()
    assert await archive.last_changed() is None


@pytest.mark.asyncio
async def test_task_last_changed_returns_cached() -> None:
    archive = make_task_archive()
    archive._last_update = T0
    assert await archive.last_changed() == T0


@pytest.mark.asyncio
async def test_task_get_projects_returns_cached() -> None:
    archive = make_task_archive()
    archive._projects = [Project(code="test", name="Test", priority=1.0)]
    result = await archive.get_projects()
    assert len(result) == 1
    assert result[0].code == "test"


@pytest.mark.asyncio
async def test_task_get_schedulable_tasks_returns_cached() -> None:
    archive = make_task_archive()
    archive._tasks = [make_task(1), make_task(2)]
    result = await archive.get_schedulable_tasks()
    assert len(result) == 2


@pytest.mark.asyncio
async def test_task_get_task_found() -> None:
    archive = make_task_archive()
    task = make_task(42)
    archive._tasks = [task]
    result = await archive.get_task(42)
    assert result is task


@pytest.mark.asyncio
async def test_task_get_task_not_found() -> None:
    archive = make_task_archive()
    archive._tasks = []
    assert await archive.get_task(999) is None


@pytest.mark.asyncio
async def test_task_last_update_time(mocker) -> None:
    archive = make_task_archive()
    mocker.patch(
        "pyobs.robotic.storage.backend.taskarchive.http_request_with_retries",
        AsyncMock(return_value={"last_task_update": "2025-11-03T23:00:00.000"}),
    )
    t = await archive.last_update_time()
    assert t.isot.startswith("2025-11-03")


@pytest.mark.asyncio
async def test_task_get_projects_from_backend(mocker) -> None:
    archive = make_task_archive()
    mocker.patch(
        "pyobs.robotic.storage.backend.taskarchive.http_request_with_retries",
        AsyncMock(return_value={"results": [{"code": "test", "name": "Test", "priority": 1.0}]}),
    )
    result = await archive._get_projects()
    assert len(result) == 1
    assert result[0].code == "test"


@pytest.mark.asyncio
async def test_task_get_tasks_from_backend(mocker) -> None:
    archive = make_task_archive()
    mocker.patch(
        "pyobs.robotic.storage.backend.taskarchive.http_request_with_retries",
        AsyncMock(return_value={"results": [{"id": 1, "name": "t1", "duration": 300}]}),
    )
    result = await archive._get_tasks()
    assert len(result) == 1
    assert result[0].name == "t1"


# ── BackendObservationArchive ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_obs_get_schedule_returns_cached() -> None:
    archive = make_obs_archive()
    obs = make_obs(make_task())
    archive._observations = ObservationList([obs])
    result = await archive.get_schedule()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_obs_get_schedule_time_ignored() -> None:
    """time parameter is unused — backend returns cached observations."""
    archive = make_obs_archive()
    obs = make_obs(make_task())
    archive._observations = ObservationList([obs])
    assert len(await archive.get_schedule(T0)) == 1
    assert len(await archive.get_schedule(T2)) == 1


@pytest.mark.asyncio
async def test_obs_get_next_returns_active() -> None:
    archive = make_obs_archive()
    obs = make_obs(make_task(), start=T0, end=T1, state=ObservationState.PENDING)
    archive._observations = ObservationList([obs])
    mid = T0 + TimeDelta(150 * u.second)
    result = await archive.get_next_observation(mid)
    assert result is not None
    assert result.task.id == 1


@pytest.mark.asyncio
async def test_obs_get_next_boundary_exclusive() -> None:
    """Backend uses strictly exclusive boundaries (start < time < end)."""
    archive = make_obs_archive()
    obs = make_obs(make_task(), start=T0, end=T1, state=ObservationState.PENDING)
    archive._observations = ObservationList([obs])
    # at exactly T0 (start), should not return
    assert await archive.get_next_observation(T0) is None
    # at exactly T1 (end), should not return
    assert await archive.get_next_observation(T1) is None


@pytest.mark.asyncio
async def test_obs_get_next_skips_non_pending() -> None:
    archive = make_obs_archive()
    obs = make_obs(make_task(), start=T0, end=T1, state=ObservationState.COMPLETED)
    archive._observations = ObservationList([obs])
    mid = T0 + TimeDelta(150 * u.second)
    assert await archive.get_next_observation(mid) is None


@pytest.mark.asyncio
async def test_obs_get_next_calls_fetch_task(mocker) -> None:
    """fetch_task is called with task_archive when provided."""
    archive = make_obs_archive()
    task = make_task()
    obs = make_obs(task, start=T0, end=T1, state=ObservationState.PENDING)
    archive._observations = ObservationList([obs])

    task_archive = MagicMock()
    mock_fetch = mocker.patch.object(Observation, "fetch_task", AsyncMock())

    mid = T0 + TimeDelta(150 * u.second)
    result = await archive.get_next_observation(mid, task_archive=task_archive)
    assert result is not None
    mock_fetch.assert_called_once_with(task_archive)


@pytest.mark.asyncio
async def test_obs_get_current_returns_in_progress() -> None:
    archive = make_obs_archive()
    obs = make_obs(make_task(), state=ObservationState.IN_PROGRESS)
    archive._observations = ObservationList([obs])
    result = await archive.get_current_observation()
    assert result is not None
    assert result.state == ObservationState.IN_PROGRESS


@pytest.mark.asyncio
async def test_obs_get_current_returns_none_when_idle() -> None:
    archive = make_obs_archive()
    obs = make_obs(make_task(), state=ObservationState.PENDING)
    archive._observations = ObservationList([obs])
    assert await archive.get_current_observation() is None


@pytest.mark.asyncio
async def test_obs_add_observations(mocker) -> None:
    archive = make_obs_archive()
    mock_request = mocker.patch(
        "pyobs.robotic.storage.backend.observationarchive.http_request_with_retries",
        AsyncMock(return_value={}),
    )
    obs = make_obs(make_task())
    await archive.add_observations(ObservationList([obs]))
    mock_request.assert_called_once()
    call_kwargs = mock_request.call_args[1]
    assert call_kwargs["method"] == "post"
    assert call_kwargs["expected_status"] == 201


@pytest.mark.asyncio
async def test_obs_clear_schedule(mocker) -> None:
    archive = make_obs_archive()
    mock_request = mocker.patch(
        "pyobs.robotic.storage.backend.observationarchive.http_request_with_retries",
        AsyncMock(return_value={}),
    )
    await archive.clear_schedule(T0)
    mock_request.assert_called_once()
    call_kwargs = mock_request.call_args[1]
    assert "after" in call_kwargs["params"]


@pytest.mark.asyncio
async def test_obs_update_observation(mocker) -> None:
    archive = make_obs_archive()
    mock_request = mocker.patch(
        "pyobs.robotic.storage.backend.observationarchive.http_request_with_retries",
        AsyncMock(return_value={}),
    )
    obs = make_obs(make_task())
    await archive.update_observation(obs)
    mock_request.assert_called_once()
    call_kwargs = mock_request.call_args[1]
    assert call_kwargs["method"] == "put"
    assert call_kwargs["expected_status"] == 200
    # URL should contain the observation's UUID
    url = mock_request.call_args[0][1]
    assert str(obs.id) in url


@pytest.mark.asyncio
async def test_obs_get_observations_builds_params(mocker) -> None:
    archive = make_obs_archive()
    mock_request = mocker.patch(
        "pyobs.robotic.storage.backend.observationarchive.http_request_with_retries",
        AsyncMock(return_value={"results": []}),
    )
    task = make_task(5)
    await archive.get_observations(
        task=task,
        state=ObservationState.PENDING,
        start_after=T0,
        end_before=T1,
    )
    params = mock_request.call_args[1]["params"]
    assert params["task"] == 5
    assert params["state"] == ObservationState.PENDING
    assert "start_after" in params
    assert "end_before" in params


@pytest.mark.asyncio
async def test_obs_last_update_time(mocker) -> None:
    archive = make_obs_archive()
    mocker.patch(
        "pyobs.robotic.storage.backend.observationarchive.http_request_with_retries",
        AsyncMock(return_value={"last_observation_update": "2025-11-03T23:00:00.000"}),
    )
    t = await archive.last_update_time()
    assert t.isot.startswith("2025-11-03")
