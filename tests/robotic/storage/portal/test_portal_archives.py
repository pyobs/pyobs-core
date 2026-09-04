from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import astropy.units as u
import pytest
from astropy.time import TimeDelta

from pyobs.robotic import Task
from pyobs.robotic.instruments import InstrumentCapabilities
from pyobs.robotic.observation import Observation, ObservationList, ObservationState
from pyobs.robotic.storage.portal.observationarchive import PortalObservationArchive
from pyobs.robotic.storage.portal.taskarchive import PortalTaskArchive
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


def make_task_archive() -> PortalTaskArchive:
    archive = PortalTaskArchive(url="http://localhost:8000", token="testtoken", auto_update=False)
    archive._aiohttp_session = MagicMock()
    return archive


def make_obs_archive() -> PortalObservationArchive:
    archive = PortalObservationArchive(url="http://localhost:8000", token="testtoken", auto_update=False)
    archive._aiohttp_session = MagicMock()
    return archive


# ── PortalTaskArchive ────────────────────────────────────────────────────────


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
        "pyobs.robotic.storage.portal.taskarchive.http_request_with_retries",
        AsyncMock(return_value={"last_task_update": "2025-11-03T23:00:00.000"}),
    )
    t = await archive.last_update_time()
    assert t.isot.startswith("2025-11-03")


@pytest.mark.asyncio
async def test_task_get_projects_from_portal(mocker) -> None:
    archive = make_task_archive()
    mock = mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(return_value=[{"code": "test", "name": "Test", "priority": 1.0}]),
    )
    result = await archive._get_projects()
    assert len(result) == 1
    assert result[0].code == "test"
    # truncated pagination must be an error, never a silently partial list applied to the cache
    assert mock.call_args[1]["strict"] is True


@pytest.mark.asyncio
async def test_task_get_projects_from_portal_accepts_public(mocker) -> None:
    """Projects with the portal `public` flag ingest without a strict-model ValidationError."""
    archive = make_task_archive()
    mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(
            return_value=[
                {"code": "public", "name": "Public", "priority": 1.0, "public": True},
                {"code": "private", "name": "Private", "priority": 1.0, "public": False},
            ]
        ),
    )
    result = await archive._get_projects()
    assert len(result) == 2
    assert result[0].code == "public"
    assert result[0].public is True
    assert result[1].code == "private"
    assert result[1].public is False


@pytest.mark.asyncio
async def test_task_get_projects_from_portal_accepts_updated_at(mocker) -> None:
    """Projects with the portal `updated_at` field (pyobs-portal#134, pyobs-core#848) ingest
    without a strict-model ValidationError, and the value round-trips."""
    archive = make_task_archive()
    mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(
            return_value=[
                {
                    "code": "test",
                    "name": "Test",
                    "priority": 1.0,
                    "updated_at": "2026-08-20T17:59:29.526066Z",
                }
            ]
        ),
    )
    result = await archive._get_projects()
    assert len(result) == 1
    assert result[0].updated_at == "2026-08-20T17:59:29.526066Z"


@pytest.mark.asyncio
async def test_task_get_tasks_from_portal(mocker) -> None:
    archive = make_task_archive()
    mock = mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(return_value=[{"id": 1, "name": "t1", "duration": 300}]),
    )
    result = await archive._get_tasks()
    assert len(result) == 1
    assert result[0].name == "t1"
    assert mock.call_args[1]["strict"] is True


@pytest.mark.asyncio
async def test_task_get_tasks_from_portal_accepts_updated_at(mocker) -> None:
    """Tasks with the portal `updated_at` field (pyobs-portal#84) ingest without a
    strict-model ValidationError, and the value round-trips."""
    archive = make_task_archive()
    mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(return_value=[{"id": 1, "name": "t1", "duration": 300, "updated_at": "2026-08-20T17:59:29.526066Z"}]),
    )
    result = await archive._get_tasks()
    assert len(result) == 1
    assert result[0].updated_at == "2026-08-20T17:59:29.526066Z"


# ── PortalObservationArchive ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_obs_get_schedule_returns_cached() -> None:
    archive = make_obs_archive()
    obs = make_obs(make_task())
    archive._observations = ObservationList([obs])
    result = await archive.get_schedule()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_obs_get_schedule_time_ignored() -> None:
    """time parameter is unused — portal returns cached observations."""
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
    """Portal uses strictly exclusive boundaries (start < time < end)."""
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


def make_unresolvable_task_archive(last_changed: Time | None = T0) -> AsyncMock:
    task_archive = AsyncMock()
    task_archive.get_task = AsyncMock(return_value=None)
    task_archive.last_changed = AsyncMock(return_value=last_changed)
    return task_archive


@pytest.mark.asyncio
async def test_obs_get_next_cancels_unresolvable_task(mocker) -> None:
    """A portal task that vanished from the active list (e.g. deactivated) resolves obs.task to
    None; the observation must be marked canceled -- with its task id preserved in the PUT
    payload, since the portal's task FK is non-nullable -- instead of skipped-and-relogged
    forever."""
    archive = make_obs_archive()
    obs = Observation(task=99, start=T0, end=T1, state=ObservationState.PENDING)
    archive._observations = ObservationList([obs])
    task_archive = make_unresolvable_task_archive()
    mock_request = mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_with_retries",
        AsyncMock(return_value={}),
    )

    mid = T0 + TimeDelta(150 * u.second)
    result = await archive.get_next_observation(mid, task_archive=task_archive)

    assert result is None
    assert obs.state == ObservationState.CANCELED
    mock_request.assert_called_once()
    assert mock_request.call_args[1]["method"] == "put"
    assert mock_request.call_args[1]["json"]["task"] == 99


@pytest.mark.asyncio
async def test_obs_get_next_skips_unresolvable_task_when_task_archive_never_polled(mocker) -> None:
    """last_changed() is None until the task archive's first successful poll -- indistinguishable
    from a genuinely removed task by get_task() alone. Must not cancel on that race (e.g. at
    startup, if the observation archive's first poll lands before the task archive's)."""
    archive = make_obs_archive()
    obs = Observation(task=99, start=T0, end=T1, state=ObservationState.PENDING)
    archive._observations = ObservationList([obs])
    task_archive = make_unresolvable_task_archive(last_changed=None)
    mock_request = mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_with_retries",
        AsyncMock(return_value={}),
    )

    mid = T0 + TimeDelta(150 * u.second)
    result = await archive.get_next_observation(mid, task_archive=task_archive)

    assert result is None
    assert obs.state == ObservationState.PENDING
    mock_request.assert_not_called()


@pytest.mark.asyncio
async def test_obs_get_current_skips_unresolvable_task_without_canceling(mocker) -> None:
    """An in-progress observation must not be canceled out from under a running mastermind even
    if its task was deactivated mid-run -- log-and-skip, same as before this fix."""
    archive = make_obs_archive()
    obs = Observation(task=99, start=T0, end=T1, state=ObservationState.IN_PROGRESS)
    archive._observations = ObservationList([obs])
    task_archive = make_unresolvable_task_archive()
    mock_request = mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_with_retries",
        AsyncMock(return_value={}),
    )

    result = await archive.get_current_observation(task_archive=task_archive)

    assert result is None
    assert obs.state == ObservationState.IN_PROGRESS
    mock_request.assert_not_called()


@pytest.mark.asyncio
async def test_obs_get_next_does_not_retry_canceled_observation_in_same_poll(mocker) -> None:
    """A second call within the same poll cycle must not re-fetch/re-cancel the same
    observation -- the local state mutation stops it matching the pending filter."""
    archive = make_obs_archive()
    obs = Observation(task=99, start=T0, end=T1, state=ObservationState.PENDING)
    archive._observations = ObservationList([obs])
    task_archive = make_unresolvable_task_archive()
    mock_request = mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_with_retries",
        AsyncMock(return_value={}),
    )

    mid = T0 + TimeDelta(150 * u.second)
    await archive.get_next_observation(mid, task_archive=task_archive)
    await archive.get_next_observation(mid, task_archive=task_archive)

    assert task_archive.get_task.await_count == 1
    mock_request.assert_called_once()


@pytest.mark.asyncio
async def test_obs_get_next_cancel_swallows_update_failure(mocker) -> None:
    """A failed cancel PUT must not propagate out of get_next_observation -- the mastermind's
    poll loop keeps running; state resyncs on the next successful update."""
    archive = make_obs_archive()
    obs = Observation(task=99, start=T0, end=T1, state=ObservationState.PENDING)
    archive._observations = ObservationList([obs])
    task_archive = make_unresolvable_task_archive()
    mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_with_retries",
        AsyncMock(side_effect=ConnectionError("portal unreachable")),
    )

    mid = T0 + TimeDelta(150 * u.second)
    result = await archive.get_next_observation(mid, task_archive=task_archive)

    assert result is None
    assert obs.state == ObservationState.CANCELED


@pytest.mark.asyncio
async def test_obs_add_observations(mocker) -> None:
    archive = make_obs_archive()
    mock_request = mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_with_retries",
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
        "pyobs.robotic.storage.portal.observationarchive.http_request_with_retries",
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
        "pyobs.robotic.storage.portal.observationarchive.http_request_with_retries",
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
        "pyobs.robotic.storage.portal.observationarchive.http_request_paginated",
        AsyncMock(return_value=[]),
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
    # truncated pagination must be an error, never a silently partial list applied to the cache
    assert mock_request.call_args[1]["strict"] is True


@pytest.mark.asyncio
async def test_obs_get_observations_tolerates_portal_archive_url(mocker) -> None:
    """pyobs-portal's ObservationSerializer emits a computed ``archive_url`` per row
    (pyobs-portal#82) -- None for the pending/in_progress states Mastermind fetches, a deep
    link for terminal ones. Observation declares the field so the payload still validates
    under ``extra="forbid"``; a validation error here used to be swallowed by
    ``_check_for_changes`` and stall the poll loop forever."""
    archive = make_obs_archive()
    mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_paginated",
        AsyncMock(
            return_value=[
                dict(OBS_DICT, id="obs-1", archive_url=None),
                dict(
                    OBS_DICT,
                    id="obs-2",
                    state="completed",
                    archive_url="https://archive.example/?start=2025-11-03T22%3A55%3A00&end=2025-11-03T23%3A10%3A00&OBSNUM=20260810-001",
                ),
            ]
        ),
    )

    result = await archive.get_observations()

    assert len(result) == 2
    assert result[0].archive_url is None
    assert result[1].archive_url == (
        "https://archive.example/?start=2025-11-03T22%3A55%3A00&end=2025-11-03T23%3A10%3A00&OBSNUM=20260810-001"
    )


@pytest.mark.asyncio
async def test_obs_last_update_time(mocker) -> None:
    archive = make_obs_archive()
    mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_with_retries",
        AsyncMock(return_value={"last_observation_update": "2025-11-03T23:00:00.000"}),
    )
    t = await archive.last_update_time()
    assert t.isot.startswith("2025-11-03")


# ── change detection: content comparison (#789/#790) + marker-gated polling (#84) ────────────────


OBS_DICT = {"task": 1, "start": T0.isot, "end": T1.isot, "state": "pending", "archive_url": None}


@pytest.mark.asyncio
async def test_task_update_not_gated_on_marker(mocker) -> None:
    """`_update()` itself does not consult the marker -- the gate lives in `_poll()`, so a direct
    download always applies. (The #789 failure mode -- the marker being per-process and stale --
    is resolved by the portal computing it from the DB; see the `_poll` tests.)"""
    archive = make_task_archive()
    marker = mocker.patch.object(archive, "last_update_time", AsyncMock(return_value=T0))
    on_tasks_changed = AsyncMock()
    archive._on_tasks_changed = on_tasks_changed
    mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(
            side_effect=[
                [{"code": "test", "name": "Test", "priority": 1.0}],  # projects
                [{"id": 1, "name": "t1", "duration": 300}],  # tasks
            ]
        ),
    )

    await archive._update()

    marker.assert_not_awaited()
    assert len(archive._projects) == 1
    assert len(archive._tasks) == 1
    assert archive._last_update is not None
    on_tasks_changed.assert_awaited_once()


@pytest.mark.asyncio
async def test_task_update_no_change_no_notification(mocker) -> None:
    """Idempotent poll: identical content must not fire on_tasks_changed or bump _last_update."""
    archive = make_task_archive()
    on_tasks_changed = AsyncMock()
    archive._on_tasks_changed = on_tasks_changed
    projects = [{"code": "test", "name": "Test", "priority": 1.0}]
    tasks = [{"id": 1, "name": "t1", "duration": 300}]
    mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(side_effect=[projects, tasks, projects, tasks]),
    )

    await archive._update()
    first_update = archive._last_update
    cached_projects = archive._projects
    cached_tasks = archive._tasks
    assert first_update is not None
    assert on_tasks_changed.await_count == 1

    await archive._update()

    assert on_tasks_changed.await_count == 1
    assert archive._last_update == first_update
    assert archive._projects is cached_projects
    assert archive._tasks is cached_tasks


@pytest.mark.asyncio
async def test_task_update_ignores_updated_at_only_change(mocker) -> None:
    """A no-op re-save (unchanged DRF PATCH still bumps `updated_at` via auto_now) must not fire
    on_tasks_changed or bump _last_update/cache -- see pyobs-core#856."""
    archive = make_task_archive()
    on_tasks_changed = AsyncMock()
    archive._on_tasks_changed = on_tasks_changed
    mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(
            side_effect=[
                [{"code": "test", "name": "Test", "priority": 1.0, "updated_at": T0.isot}],
                [{"id": 1, "name": "t1", "duration": 300, "updated_at": T0.isot}],
                [{"code": "test", "name": "Test", "priority": 1.0, "updated_at": T1.isot}],
                [{"id": 1, "name": "t1", "duration": 300, "updated_at": T1.isot}],
            ]
        ),
    )

    await archive._update()
    first_update = archive._last_update
    cached_projects = archive._projects
    cached_tasks = archive._tasks
    assert first_update is not None
    assert on_tasks_changed.await_count == 1

    await archive._update()

    assert on_tasks_changed.await_count == 1
    assert archive._last_update == first_update
    assert archive._projects is cached_projects
    assert archive._tasks is cached_tasks


@pytest.mark.asyncio
async def test_task_update_detects_content_change(mocker) -> None:
    """Same task identity but changed content (e.g. active=False in the portal) must be applied."""
    archive = make_task_archive()
    on_tasks_changed = AsyncMock()
    archive._on_tasks_changed = on_tasks_changed
    mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(
            side_effect=[
                [{"code": "test", "name": "Test", "priority": 1.0}],
                [{"id": 1, "name": "t1", "duration": 300}],
                [{"code": "test", "name": "Test", "priority": 1.0}],
                [{"id": 1, "name": "t1", "duration": 300, "active": False}],
            ]
        ),
    )

    await archive._update()
    assert on_tasks_changed.await_count == 1
    assert archive._tasks[0].active is True

    await archive._update()

    assert on_tasks_changed.await_count == 2
    assert archive._tasks[0].active is False


@pytest.mark.asyncio
async def test_task_update_ignores_runtime_attributes(mocker) -> None:
    """Change detection must compare model fields, not pydantic __eq__: runtime attributes such as
    Task._cant_run_reason (set by can_run()) land in __dict__ and would make an unchanged task look
    changed on every poll."""
    archive = make_task_archive()
    on_tasks_changed = AsyncMock()
    archive._on_tasks_changed = on_tasks_changed
    tasks = [{"id": 1, "name": "t1", "duration": 300}]
    projects = [{"code": "test", "name": "Test", "priority": 1.0}]
    mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(side_effect=[projects, tasks, projects, tasks]),
    )

    await archive._update()
    # simulate the mastermind having run can_run() on the cached task
    archive._tasks[0]._cant_run_reason = "weather is bad"
    assert archive._tasks[0] != Task(id=1, name="t1", duration=300)  # __eq__ sees the attr

    await archive._update()

    assert on_tasks_changed.await_count == 1
    assert archive._tasks[0]._cant_run_reason == "weather is bad"  # cache untouched


@pytest.mark.asyncio
async def test_obs_update_downloads_and_applies(mocker) -> None:
    """New observations appear in the cache on the next poll."""
    archive = make_obs_archive()
    mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_paginated",
        AsyncMock(side_effect=[[OBS_DICT], [OBS_DICT], [OBS_DICT]]),
    )

    await archive._update()
    assert archive._last_update is not None
    assert len(archive._observations) == 1

    await archive._update()
    assert len(archive._observations) == 1


@pytest.mark.asyncio
async def test_obs_update_announces_by_default(mocker, caplog) -> None:
    """Default (announce_updates=True) behavior, e.g. as used by Mastermind: a real content
    change logs an INFO line."""
    archive = make_obs_archive()
    mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_paginated",
        AsyncMock(return_value=[OBS_DICT]),
    )

    with caplog.at_level("INFO"):
        await archive._update()

    assert "Downloaded new schedule" in caplog.text


@pytest.mark.asyncio
async def test_obs_update_announce_updates_false_suppresses_info_log(mocker, caplog) -> None:
    """Scheduler injects announce_updates=False (it already logs its own schedule in detail) --
    the change must still be applied, just not announced at INFO."""
    archive = PortalObservationArchive(
        url="http://localhost:8000", token="testtoken", auto_update=False, announce_updates=False
    )
    archive._aiohttp_session = MagicMock()
    mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_paginated",
        AsyncMock(return_value=[OBS_DICT]),
    )

    with caplog.at_level("INFO"):
        await archive._update()

    assert len(archive._observations) == 1
    assert "Downloaded new schedule" not in caplog.text


@pytest.mark.asyncio
async def test_obs_update_no_change_keeps_cache(mocker) -> None:
    """Idempotent poll must not replace the cached list or bump _last_update."""
    archive = make_obs_archive()
    mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_paginated",
        AsyncMock(side_effect=[[OBS_DICT], [OBS_DICT]]),
    )

    await archive._update()
    cached = archive._observations
    first_update = archive._last_update
    assert first_update is not None

    await archive._update()

    assert archive._observations is cached
    assert archive._last_update == first_update


@pytest.mark.asyncio
async def test_obs_update_detects_state_transition_in_fetched_set(mocker) -> None:
    """An in-set state transition (pending -> in_progress, both within the portal's
    state=pending,in_progress filter) must be picked up even though Observation.__eq__ ignores
    state -- the comparison covers the full dumped content."""
    # sanity: plain __eq__ misses the state change entirely (same task id/start/end)
    pending = Observation(task=make_task(), start=T0, end=T1, state=ObservationState.PENDING)
    in_progress = Observation(task=make_task(), start=T0, end=T1, state=ObservationState.IN_PROGRESS)
    assert pending == in_progress

    archive = make_obs_archive()
    mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_paginated",
        AsyncMock(side_effect=[[OBS_DICT], [dict(OBS_DICT, state="in_progress")]]),
    )

    await archive._update()
    assert archive._observations[0].state == ObservationState.PENDING

    await archive._update()

    assert archive._observations[0].state == ObservationState.IN_PROGRESS


@pytest.mark.asyncio
async def test_obs_update_applies_shrinkage_when_observation_disappears(mocker) -> None:
    """The production path for the window_expired symptom from #789: the portal's server-side
    state=pending,in_progress and end_after=now filters drop the expired observation from the
    response, and the unconditional refetch must apply that shrinkage -- otherwise the mastermind
    keeps treating the window-expired observation as runnable."""
    archive = make_obs_archive()
    mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_paginated",
        AsyncMock(side_effect=[[OBS_DICT], []]),
    )

    await archive._update()
    assert len(archive._observations) == 1

    await archive._update()

    assert len(archive._observations) == 0


@pytest.mark.asyncio
async def test_task_update_order_insensitive(mocker) -> None:
    """The same items in a different order (e.g. an unordered portal queryset) must not be
    reported as a change -- the comparison is keyed by ID."""
    archive = make_task_archive()
    on_tasks_changed = AsyncMock()
    archive._on_tasks_changed = on_tasks_changed
    projects = [{"code": "a", "name": "A", "priority": 1.0}, {"code": "b", "name": "B", "priority": 1.0}]
    tasks = [{"id": 1, "name": "t1", "duration": 300}, {"id": 2, "name": "t2", "duration": 300}]
    mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(side_effect=[projects, tasks, list(reversed(projects)), list(reversed(tasks))]),
    )

    await archive._update()
    assert on_tasks_changed.await_count == 1

    await archive._update()

    assert on_tasks_changed.await_count == 1


@pytest.mark.asyncio
async def test_obs_update_order_insensitive(mocker) -> None:
    """The same observations in a different order must not be reported as a change."""
    archive = make_obs_archive()
    obs_a = {"id": "obs-a", "task": 1, "start": T0.isot, "end": T1.isot, "state": "pending"}
    obs_b = {"id": "obs-b", "task": 1, "start": T1.isot, "end": T2.isot, "state": "pending"}
    mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_paginated",
        AsyncMock(side_effect=[[obs_a, obs_b], [obs_b, obs_a]]),
    )

    await archive._update()
    assert archive._last_update is not None
    cached = archive._observations

    await archive._update()

    assert archive._observations is cached  # reordering is not a change


@pytest.mark.asyncio
async def test_obs_update_normalizes_task_id(mocker) -> None:
    """Cached observations get their task replaced by a full Task object when the mastermind calls
    fetch_task(); a fresh download carries the plain FK id. The use_task_id dump normalization must
    keep both sides comparable, so this is not reported as a change."""
    archive = make_obs_archive()
    # seed cache the way the mastermind leaves it: task resolved to a full Task object
    archive._observations = ObservationList([make_obs(make_task())])
    mocker.patch(
        "pyobs.robotic.storage.portal.observationarchive.http_request_paginated",
        AsyncMock(side_effect=[[OBS_DICT]]),
    )

    await archive._update()

    assert archive._last_update is None  # nothing changed -> marker not touched
    assert archive._observations[0].task is not None


# ── marker-gated polling (#84: last_*_update markers are DB-derived and truthful again) ───────────


@pytest.mark.asyncio
async def test_task_poll_downloads_on_first_poll(mocker) -> None:
    """First poll: no cached marker -> download and remember the marker."""
    archive = make_task_archive()
    mocker.patch.object(archive, "last_update_time", AsyncMock(return_value=T1))
    update = mocker.patch.object(archive, "_update", AsyncMock())
    await archive._poll()
    update.assert_awaited_once()
    assert archive._last_marker == T1


@pytest.mark.asyncio
async def test_task_poll_skips_when_marker_unchanged(mocker) -> None:
    """Marker did not move -> no download (no spurious re-download/comparison)."""
    archive = make_task_archive()
    archive._last_marker = T1
    mocker.patch.object(archive, "last_update_time", AsyncMock(return_value=T1))
    update = mocker.patch.object(archive, "_update", AsyncMock())
    await archive._poll()
    update.assert_not_awaited()
    assert archive._last_marker == T1


@pytest.mark.asyncio
async def test_task_poll_downloads_when_marker_newer(mocker) -> None:
    """Marker moved -> download and advance the cached marker."""
    archive = make_task_archive()
    archive._last_marker = T1
    mocker.patch.object(archive, "last_update_time", AsyncMock(return_value=T2))
    update = mocker.patch.object(archive, "_update", AsyncMock())
    await archive._poll()
    update.assert_awaited_once()
    assert archive._last_marker == T2


@pytest.mark.asyncio
async def test_obs_poll_downloads_on_first_poll(mocker) -> None:
    archive = make_obs_archive()
    mocker.patch.object(archive, "last_update_time", AsyncMock(return_value=T1))
    update = mocker.patch.object(archive, "_update", AsyncMock())
    await archive._poll()
    update.assert_awaited_once()
    assert archive._last_marker == T1


@pytest.mark.asyncio
async def test_obs_poll_skips_when_marker_unchanged(mocker) -> None:
    archive = make_obs_archive()
    archive._last_marker = T1
    mocker.patch.object(archive, "last_update_time", AsyncMock(return_value=T1))
    update = mocker.patch.object(archive, "_update", AsyncMock())
    await archive._poll()
    update.assert_not_awaited()
    assert archive._last_marker == T1


@pytest.mark.asyncio
async def test_obs_poll_downloads_when_marker_newer(mocker) -> None:
    archive = make_obs_archive()
    archive._last_marker = T1
    mocker.patch.object(archive, "last_update_time", AsyncMock(return_value=T2))
    update = mocker.patch.object(archive, "_update", AsyncMock())
    await archive._poll()
    update.assert_awaited_once()
    assert archive._last_marker == T2


# ── instrument-capabilities poll (§A.4) ─────────────────────────────────────────


def test_get_instrument_capabilities_defaults_to_none() -> None:
    archive = make_task_archive()
    assert archive.get_instrument_capabilities() is None


@pytest.mark.asyncio
async def test_instrument_capabilities_poll_downloads_on_first_poll(mocker) -> None:
    archive = make_task_archive()
    mocker.patch.object(archive, "_last_instrument_update_time", AsyncMock(return_value=T1))
    mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(return_value=[{"display_name": "Test", "cameras": []}]),
    )
    await archive._poll_instrument_capabilities()

    capabilities = archive.get_instrument_capabilities()
    assert isinstance(capabilities, InstrumentCapabilities)
    assert len(capabilities.instruments) == 1
    assert archive._instrument_capabilities_marker == T1


@pytest.mark.asyncio
async def test_instrument_capabilities_poll_skips_when_marker_unchanged(mocker) -> None:
    archive = make_task_archive()
    archive._instrument_capabilities_marker = T1
    mocker.patch.object(archive, "_last_instrument_update_time", AsyncMock(return_value=T1))
    fetch = mocker.patch("pyobs.robotic.storage.portal.taskarchive.http_request_paginated", AsyncMock())
    await archive._poll_instrument_capabilities()
    fetch.assert_not_awaited()
    assert archive._instrument_capabilities_marker == T1


@pytest.mark.asyncio
async def test_instrument_capabilities_poll_downloads_when_marker_newer(mocker) -> None:
    archive = make_task_archive()
    archive._instrument_capabilities_marker = T1
    mocker.patch.object(archive, "_last_instrument_update_time", AsyncMock(return_value=T2))
    fetch = mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(return_value=[{"display_name": "Test", "cameras": []}]),
    )
    await archive._poll_instrument_capabilities()
    fetch.assert_awaited_once()
    assert archive._instrument_capabilities_marker == T2


@pytest.mark.asyncio
async def test_instrument_capabilities_poll_downloads_when_marker_moves_backward(mocker) -> None:
    """Deleting the row that held the current max(updated_at) moves the marker backward -- a
    strict `>` comparison would miss this and leave the removed device cached indefinitely."""
    archive = make_task_archive()
    archive._instrument_capabilities_marker = T2
    mocker.patch.object(archive, "_last_instrument_update_time", AsyncMock(return_value=T1))
    fetch = mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(return_value=[{"display_name": "Test", "cameras": []}]),
    )
    await archive._poll_instrument_capabilities()
    fetch.assert_awaited_once()
    assert archive._instrument_capabilities_marker == T1


@pytest.mark.asyncio
async def test_instrument_capabilities_poll_keeps_last_good_on_marker_fetch_failure(mocker) -> None:
    archive = make_task_archive()
    good = InstrumentCapabilities.from_api_response([{"display_name": "Good"}])
    archive._instrument_capabilities = good
    archive._instrument_capabilities_marker = T1
    mocker.patch.object(archive, "_last_instrument_update_time", AsyncMock(side_effect=ConnectionError("unreachable")))
    await archive._poll_instrument_capabilities()
    assert archive.get_instrument_capabilities() is good
    assert archive._instrument_capabilities_marker == T1


@pytest.mark.asyncio
async def test_instrument_capabilities_poll_keeps_last_good_on_download_failure(mocker) -> None:
    archive = make_task_archive()
    good = InstrumentCapabilities.from_api_response([{"display_name": "Good"}])
    archive._instrument_capabilities = good
    archive._instrument_capabilities_marker = T1
    mocker.patch.object(archive, "_last_instrument_update_time", AsyncMock(return_value=T2))
    mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(side_effect=ConnectionError("unreachable")),
    )
    await archive._poll_instrument_capabilities()
    assert archive.get_instrument_capabilities() is good
    assert archive._instrument_capabilities_marker == T1  # not advanced -- retry next poll


@pytest.mark.asyncio
async def test_instrument_capabilities_poll_tolerates_unrecognized_fields(mocker) -> None:
    """A portal running ahead of this pyobs-core release (e.g. the model/sensor_type fields
    added to CameraCapability/FilterWheelCapability) must not turn into a hard parse failure --
    the capability models use extra="ignore" (not BaseModel's default extra="forbid") for
    exactly this: an unrecognized field is dropped, everything else still parses and the poll
    succeeds normally, advancing the marker rather than falling back to the last-good cache."""
    archive = make_task_archive()
    stale = InstrumentCapabilities.from_api_response([{"display_name": "Stale"}])
    archive._instrument_capabilities = stale
    archive._instrument_capabilities_marker = T1
    mocker.patch.object(archive, "_last_instrument_update_time", AsyncMock(return_value=T2))
    mocker.patch(
        "pyobs.robotic.storage.portal.taskarchive.http_request_paginated",
        AsyncMock(return_value=[{"display_name": "Fresh", "some_unrecognized_future_field": 1, "cameras": []}]),
    )
    await archive._poll_instrument_capabilities()

    capabilities = archive.get_instrument_capabilities()
    assert capabilities is not stale
    assert isinstance(capabilities, InstrumentCapabilities)
    assert capabilities.instruments[0].display_name == "Fresh"
    assert archive._instrument_capabilities_marker == T2


@pytest.mark.asyncio
async def test_poll_calls_instrument_capabilities_poll(mocker) -> None:
    """_poll() (the background loop's entry point) must not forget to also poll instrument
    capabilities alongside tasks/projects."""
    archive = make_task_archive()
    mocker.patch.object(archive, "last_update_time", AsyncMock(return_value=T1))
    mocker.patch.object(archive, "_update", AsyncMock())
    instrument_poll = mocker.patch.object(archive, "_poll_instrument_capabilities", AsyncMock())
    await archive._poll()
    instrument_poll.assert_awaited_once()
