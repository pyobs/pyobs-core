from __future__ import annotations

import astropy.units as u
import pytest
from astropy.time import TimeDelta

from pyobs.robotic import Task
from pyobs.robotic.memory import MemoryObservationArchive, MemoryTaskArchive
from pyobs.robotic.observation import Observation, ObservationList, ObservationState
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.robotic.task import Project
from pyobs.utils.time import Time

# ── fixtures ──────────────────────────────────────────────────────────────────

T0 = Time("2025-11-03T23:00:00", scale="utc")
T1 = T0 + TimeDelta(300 * u.second)
T2 = T1 + TimeDelta(300 * u.second)
T3 = T2 + TimeDelta(300 * u.second)


def make_task(task_id: int = 1) -> Task:
    return Task(id=task_id, name=f"task_{task_id}", duration=300)


def make_obs(
    task: Task, start: Time = T0, end: Time = T1, state: ObservationState = ObservationState.PENDING
) -> Observation:
    return Observation(task=task, start=start, end=end, state=state)


@pytest.fixture
def obs_archive() -> MemoryObservationArchive:
    return MemoryObservationArchive()


@pytest.fixture
def task_archive() -> MemoryTaskArchive:
    return MemoryTaskArchive()


# ── MemoryObservationArchive ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_obs_add_and_get_schedule(obs_archive) -> None:
    obs = make_obs(make_task())
    await obs_archive.add_observations(ObservationList([obs]))
    loaded = await obs_archive.get_schedule()
    assert len(loaded) == 1
    assert loaded[0].task.id == 1


@pytest.mark.asyncio
async def test_obs_get_schedule_returns_copy(obs_archive) -> None:
    """Mutations to the returned list don't affect the archive."""
    obs = make_obs(make_task())
    await obs_archive.add_observations(ObservationList([obs]))
    loaded = await obs_archive.get_schedule()
    loaded.clear()
    assert len(await obs_archive.get_schedule()) == 1


@pytest.mark.asyncio
async def test_obs_get_schedule_time_ignored(obs_archive) -> None:
    """time parameter is unused — all observations are returned."""
    obs = make_obs(make_task())
    await obs_archive.add_observations(ObservationList([obs]))
    assert len(await obs_archive.get_schedule(T0)) == 1
    assert len(await obs_archive.get_schedule(T2)) == 1


@pytest.mark.asyncio
async def test_obs_add_empty_is_noop(obs_archive) -> None:
    await obs_archive.add_observations(ObservationList())
    assert len(await obs_archive.get_schedule()) == 0


@pytest.mark.asyncio
async def test_obs_clear_removes_pending(obs_archive) -> None:
    pending = make_obs(make_task(1), start=T0, end=T1, state=ObservationState.PENDING)
    completed = make_obs(make_task(2), start=T1, end=T2, state=ObservationState.COMPLETED)
    await obs_archive.add_observations(ObservationList([pending, completed]))

    await obs_archive.clear_schedule(T0)

    loaded = await obs_archive.get_schedule()
    assert not any(o.state == ObservationState.PENDING for o in loaded)
    assert any(o.state == ObservationState.COMPLETED for o in loaded)


@pytest.mark.asyncio
async def test_obs_clear_keeps_past_pending(obs_archive) -> None:
    """Pending observations that ended before start_time are kept."""
    past = make_obs(
        make_task(),
        start=T0 - TimeDelta(600 * u.second),
        end=T0 - TimeDelta(300 * u.second),
        state=ObservationState.PENDING,
    )
    await obs_archive.add_observations(ObservationList([past]))

    await obs_archive.clear_schedule(T0)
    assert len(await obs_archive.get_schedule()) == 1


@pytest.mark.asyncio
async def test_obs_get_next_returns_active(obs_archive) -> None:
    obs = make_obs(make_task(), start=T0, end=T1, state=ObservationState.PENDING)
    await obs_archive.add_observations(ObservationList([obs]))

    mid = T0 + TimeDelta(150 * u.second)
    result = await obs_archive.get_next_observation(mid)
    assert result is not None
    assert result.task.id == 1


@pytest.mark.asyncio
async def test_obs_get_next_returns_none_before_window(obs_archive) -> None:
    obs = make_obs(make_task(), start=T1, end=T2, state=ObservationState.PENDING)
    await obs_archive.add_observations(ObservationList([obs]))
    assert await obs_archive.get_next_observation(T0) is None


@pytest.mark.asyncio
async def test_obs_get_next_returns_none_after_window(obs_archive) -> None:
    obs = make_obs(make_task(), start=T0, end=T1, state=ObservationState.PENDING)
    await obs_archive.add_observations(ObservationList([obs]))
    assert await obs_archive.get_next_observation(T2) is None


@pytest.mark.asyncio
async def test_obs_get_next_skips_non_pending(obs_archive) -> None:
    obs = make_obs(make_task(), start=T0, end=T1, state=ObservationState.COMPLETED)
    await obs_archive.add_observations(ObservationList([obs]))

    mid = T0 + TimeDelta(150 * u.second)
    assert await obs_archive.get_next_observation(mid) is None


@pytest.mark.asyncio
async def test_obs_get_next_calls_fetch_task(obs_archive) -> None:
    """fetch_task is called when task_archive is provided."""
    task = make_task()
    obs = make_obs(task, start=T0, end=T1, state=ObservationState.PENDING)
    await obs_archive.add_observations(ObservationList([obs]))

    task_archive = MemoryTaskArchive([task])
    mid = T0 + TimeDelta(150 * u.second)
    result = await obs_archive.get_next_observation(mid, task_archive=task_archive)
    assert result is not None


@pytest.mark.asyncio
async def test_obs_get_next_restores_resolved_target(obs_archive) -> None:
    """get_next_observation restores resolved target via fetch_task."""
    task = make_task()
    resolved = SiderealTarget(name="Vega", ra=279.23, dec=38.78)
    obs = make_obs(task, start=T0, end=T1, state=ObservationState.PENDING)
    obs.target = resolved
    await obs_archive.add_observations(ObservationList([obs]))

    task_archive = MemoryTaskArchive([task])
    mid = T0 + TimeDelta(150 * u.second)
    result = await obs_archive.get_next_observation(mid, task_archive=task_archive)

    assert result is not None
    assert isinstance(result.task.target, SiderealTarget)
    assert result.task.target.name == "Vega"


@pytest.mark.asyncio
async def test_obs_get_current_returns_in_progress(obs_archive) -> None:
    obs = make_obs(make_task(), state=ObservationState.IN_PROGRESS)
    await obs_archive.add_observations(ObservationList([obs]))
    result = await obs_archive.get_current_observation()
    assert result is not None
    assert result.state == ObservationState.IN_PROGRESS


@pytest.mark.asyncio
async def test_obs_get_current_returns_none_when_idle(obs_archive) -> None:
    obs = make_obs(make_task(), state=ObservationState.PENDING)
    await obs_archive.add_observations(ObservationList([obs]))
    assert await obs_archive.get_current_observation() is None


@pytest.mark.asyncio
async def test_obs_update_modifies_existing(obs_archive) -> None:
    obs = make_obs(make_task(), state=ObservationState.PENDING)
    await obs_archive.add_observations(ObservationList([obs]))

    obs.state = ObservationState.COMPLETED
    await obs_archive.update_observation(obs)

    loaded = await obs_archive.get_schedule()
    assert loaded[0].state == ObservationState.COMPLETED


@pytest.mark.asyncio
async def test_obs_update_appends_if_not_found(obs_archive) -> None:
    obs = make_obs(make_task())
    await obs_archive.update_observation(obs)
    assert len(await obs_archive.get_schedule()) == 1


@pytest.mark.asyncio
async def test_obs_get_observations_filters_state(obs_archive) -> None:
    await obs_archive.add_observations(
        ObservationList(
            [
                make_obs(make_task(1), state=ObservationState.PENDING),
                make_obs(make_task(2), start=T1, end=T2, state=ObservationState.COMPLETED),
            ]
        )
    )

    result = await obs_archive.get_observations(state=ObservationState.COMPLETED)
    assert len(result) == 1
    assert result[0].state == ObservationState.COMPLETED


@pytest.mark.asyncio
async def test_obs_get_observations_filters_task(obs_archive) -> None:
    task1, task2 = make_task(1), make_task(2)
    await obs_archive.add_observations(
        ObservationList(
            [
                make_obs(task1),
                make_obs(task2, start=T1, end=T2),
            ]
        )
    )

    result = await obs_archive.get_observations(task=task1)
    assert len(result) == 1
    assert result[0].task.id == 1


@pytest.mark.asyncio
async def test_obs_get_observations_filters_time_range(obs_archive) -> None:
    await obs_archive.add_observations(
        ObservationList(
            [
                make_obs(make_task(1), start=T0, end=T1),
                make_obs(make_task(2), start=T1, end=T2),
                make_obs(make_task(3), start=T2, end=T3),
            ]
        )
    )

    result = await obs_archive.get_observations(start_after=T1)
    assert all(o.start >= T1 for o in result)


# ── MemoryTaskArchive ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_task_last_changed_none_initially(task_archive) -> None:
    assert await task_archive.last_changed() is None


@pytest.mark.asyncio
async def test_task_get_schedulable_empty(task_archive) -> None:
    assert await task_archive.get_schedulable_tasks() == []


@pytest.mark.asyncio
async def test_task_constructed_with_tasks() -> None:
    tasks = [make_task(1), make_task(2)]
    archive = MemoryTaskArchive(tasks=tasks)
    result = await archive.get_schedulable_tasks()
    assert len(result) == 2


@pytest.mark.asyncio
async def test_task_get_task_found(task_archive) -> None:
    task = make_task(42)
    task_archive._tasks = {"42": task}
    result = await task_archive.get_task(42)
    assert result is task


@pytest.mark.asyncio
async def test_task_get_task_not_found(task_archive) -> None:
    assert await task_archive.get_task(999) is None


@pytest.mark.asyncio
async def test_task_get_task_string_id(task_archive) -> None:
    """get_task works with both int and string IDs."""
    task = make_task(1)
    task_archive._tasks = {"1": task}
    assert await task_archive.get_task("1") is task
    assert await task_archive.get_task(1) is task


@pytest.mark.asyncio
async def test_task_get_projects_empty(task_archive) -> None:
    assert await task_archive.get_projects() == []


@pytest.mark.asyncio
async def test_task_get_projects_with_projects() -> None:
    projects = [Project(code="test", name="Test", priority=1.0)]
    archive = MemoryTaskArchive(projects=projects)
    result = await archive.get_projects()
    assert len(result) == 1
    assert result[0].code == "test"


def test_task_add_task(task_archive) -> None:
    task = make_task(1)
    task_archive.add_task(task)
    assert "1" in task_archive._tasks
    assert task_archive._last_changed is not None


def test_task_add_task_replaces_existing(task_archive) -> None:
    task1 = make_task(1)
    task2 = Task(id=1, name="replaced", duration=100)
    task_archive.add_task(task1)
    task_archive.add_task(task2)
    assert task_archive._tasks["1"].name == "replaced"


def test_task_remove_task(task_archive) -> None:
    task = make_task(1)
    task_archive.add_task(task)
    task_archive.remove_task(1)
    assert "1" not in task_archive._tasks
    assert task_archive._last_changed is not None


def test_task_remove_task_noop_if_not_found(task_archive) -> None:
    task_archive.remove_task(999)  # should not raise
