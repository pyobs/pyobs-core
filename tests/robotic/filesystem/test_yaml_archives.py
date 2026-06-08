from __future__ import annotations

import glob
import os
from unittest.mock import MagicMock

import astropy.units as u
import pytest
import yaml
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import TimeDelta
from filelock import FileLock

from pyobs.robotic import Task
from pyobs.robotic.filesystem.observationarchive import YamlObservationArchive
from pyobs.robotic.filesystem.taskarchive import YamlTaskArchive
from pyobs.robotic.observation import Observation, ObservationList, ObservationState
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.utils.time import Time

# ── shared setup ──────────────────────────────────────────────────────────────

SAAO = Observer(location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m))

NIGHT = Time("2025-11-03T23:00:00", scale="utc")
OBS_START = NIGHT
OBS_END = NIGHT + TimeDelta(300 * u.second)


def make_obs_archive(tmp_path, mode="night") -> YamlObservationArchive:
    archive = YamlObservationArchive.__new__(YamlObservationArchive)
    archive._comm = None
    archive._vfs = None
    archive._timezone = None
    archive._location = None
    archive._observer = SAAO
    archive._path = str(tmp_path)
    archive._extension = "yaml"
    archive._mode = mode
    archive._lock = FileLock(os.path.join(str(tmp_path), ".lock"))
    return archive


def make_task(task_id: int = 1) -> Task:
    return Task(id=task_id, name=f"task_{task_id}", duration=300)


def make_obs(
    task: Task, start: Time = OBS_START, end: Time = OBS_END, state: ObservationState = ObservationState.PENDING
) -> Observation:
    return Observation(task=task, start=start, end=end, state=state)


# ── YamlObservationArchive ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_and_load_observations(tmp_path) -> None:
    archive = make_obs_archive(tmp_path)
    obs = make_obs(make_task())

    await archive.add_observations(ObservationList([obs]))
    loaded = await archive.get_schedule(NIGHT)

    assert len(loaded) == 1
    assert loaded[0].task.id == 1


@pytest.mark.asyncio
async def test_add_empty_list_is_noop(tmp_path) -> None:
    archive = make_obs_archive(tmp_path)
    await archive.add_observations(ObservationList())
    loaded = await archive.get_schedule()
    assert len(loaded) == 0


@pytest.mark.asyncio
async def test_add_multiple_observations(tmp_path) -> None:
    archive = make_obs_archive(tmp_path)
    t2_start = OBS_END
    t2_end = t2_start + TimeDelta(300 * u.second)
    obs1 = make_obs(make_task(1))
    obs2 = make_obs(make_task(2), start=t2_start, end=t2_end)

    await archive.add_observations(ObservationList([obs1, obs2]))
    loaded = await archive.get_schedule(NIGHT)
    assert len(loaded) == 2


@pytest.mark.asyncio
async def test_clear_schedule_removes_future_pending(tmp_path) -> None:
    archive = make_obs_archive(tmp_path)
    pending = make_obs(make_task(1), state=ObservationState.PENDING)
    t2_start = OBS_END
    t2_end = t2_start + TimeDelta(300 * u.second)
    completed = make_obs(make_task(2), start=t2_start, end=t2_end, state=ObservationState.COMPLETED)

    await archive.add_observations(ObservationList([pending, completed]))
    await archive.clear_schedule(NIGHT)

    loaded = await archive.get_schedule()
    assert not any(obs.state == ObservationState.PENDING and obs.end > NIGHT for obs in loaded)


@pytest.mark.asyncio
async def test_get_next_observation_returns_current(tmp_path) -> None:
    archive = make_obs_archive(tmp_path)
    obs = make_obs(make_task(), state=ObservationState.PENDING)
    await archive.add_observations(ObservationList([obs]))

    result = await archive.get_next_observation(OBS_START + TimeDelta(30 * u.second))
    assert result is not None
    assert result.task.id == 1


@pytest.mark.asyncio
async def test_get_next_observation_returns_none_before_window(tmp_path) -> None:
    archive = make_obs_archive(tmp_path)
    obs = make_obs(make_task(), state=ObservationState.PENDING)
    await archive.add_observations(ObservationList([obs]))

    result = await archive.get_next_observation(NIGHT - TimeDelta(3600 * u.second))
    assert result is None


@pytest.mark.asyncio
async def test_get_next_observation_skips_non_pending(tmp_path) -> None:
    archive = make_obs_archive(tmp_path)
    obs = make_obs(make_task(), state=ObservationState.COMPLETED)
    await archive.add_observations(ObservationList([obs]))

    result = await archive.get_next_observation(OBS_START + TimeDelta(30 * u.second))
    assert result is None


@pytest.mark.asyncio
async def test_get_current_observation_returns_in_progress(tmp_path) -> None:
    archive = make_obs_archive(tmp_path)
    obs = make_obs(make_task(), state=ObservationState.IN_PROGRESS)
    await archive.add_observations(ObservationList([obs]))

    result = await archive.get_current_observation(time=NIGHT)
    assert result is not None
    assert result.state == ObservationState.IN_PROGRESS


@pytest.mark.asyncio
async def test_get_current_observation_returns_none_when_idle(tmp_path) -> None:
    archive = make_obs_archive(tmp_path)
    obs = make_obs(make_task(), state=ObservationState.PENDING)
    await archive.add_observations(ObservationList([obs]))

    result = await archive.get_current_observation()
    assert result is None


@pytest.mark.asyncio
async def test_update_observation_modifies_existing(tmp_path) -> None:
    archive = make_obs_archive(tmp_path)
    obs = make_obs(make_task(), state=ObservationState.PENDING)
    await archive.add_observations(ObservationList([obs]))

    obs.state = ObservationState.COMPLETED
    await archive.update_observation(obs)

    loaded = await archive.get_schedule(NIGHT)
    assert loaded[0].state == ObservationState.COMPLETED


@pytest.mark.asyncio
async def test_update_observation_appends_if_not_found(tmp_path) -> None:
    archive = make_obs_archive(tmp_path)
    obs = make_obs(make_task())
    await archive.update_observation(obs)

    loaded = await archive.get_schedule(NIGHT)
    assert len(loaded) == 1


@pytest.mark.asyncio
async def test_get_observations_filters_by_state(tmp_path) -> None:
    archive = make_obs_archive(tmp_path)
    t2_start = OBS_END
    t2_end = t2_start + TimeDelta(300 * u.second)
    pending = make_obs(make_task(1), state=ObservationState.PENDING)
    completed = make_obs(make_task(2), start=t2_start, end=t2_end, state=ObservationState.COMPLETED)
    await archive.add_observations(ObservationList([pending, completed]))

    result = await archive.get_observations(state=ObservationState.COMPLETED)
    assert len(result) == 1
    assert result[0].state == ObservationState.COMPLETED


@pytest.mark.asyncio
async def test_get_observations_filters_by_task(tmp_path) -> None:
    archive = make_obs_archive(tmp_path)
    task1, task2 = make_task(1), make_task(2)
    t2_start = OBS_END
    t2_end = t2_start + TimeDelta(300 * u.second)
    await archive.add_observations(
        ObservationList(
            [
                make_obs(task1),
                make_obs(task2, start=t2_start, end=t2_end),
            ]
        )
    )

    result = await archive.get_observations(task=task1)
    assert len(result) == 1
    assert result[0].task.id == 1


@pytest.mark.asyncio
async def test_get_filename_night_mode(tmp_path) -> None:
    archive = make_obs_archive(tmp_path, mode="night")
    filename = archive._get_filename(NIGHT)
    assert filename.endswith(".yaml")
    assert len(filename) == len("2025-11-03.yaml")


@pytest.mark.asyncio
async def test_get_filename_day_mode(tmp_path) -> None:
    archive = make_obs_archive(tmp_path, mode="day")
    day_time = Time("2025-11-03T12:00:00", scale="utc")
    filename = archive._get_filename(day_time)
    assert filename.endswith(".yaml")


@pytest.mark.asyncio
async def test_observations_persisted_to_yaml(tmp_path) -> None:
    """Verify observations are actually written to disk in valid YAML."""
    archive = make_obs_archive(tmp_path)
    obs = make_obs(make_task())
    await archive.add_observations(ObservationList([obs]))

    yaml_files = list(tmp_path.glob("*.yaml"))
    assert len(yaml_files) == 1

    with open(yaml_files[0]) as f:
        data = yaml.safe_load(f)
    assert isinstance(data, list)
    assert len(data) == 1


# ── YamlTaskArchive ───────────────────────────────────────────────────────────

TASK_YAML = """\
id: 1
name: Kochab
duration: 300
target:
  class: pyobs.robotic.scheduler.targets.SiderealTarget
  name: Kochab
  ra: 222.676
  dec: 74.155
"""


def make_task_archive(tmp_path) -> YamlTaskArchive:
    archive = YamlTaskArchive.__new__(YamlTaskArchive)
    archive._comm = None
    archive._observer = None
    archive._timezone = None
    archive._location = None
    archive._path = str(tmp_path)
    archive._extension = "yaml"

    vfs = MagicMock()

    async def read_yaml(path):
        with open(path) as f:
            return yaml.safe_load(f)

    async def find(path, pattern):
        matches = glob.glob(os.path.join(path, pattern))
        return [os.path.basename(f) for f in matches]

    vfs.read_yaml = read_yaml
    vfs.find = find
    archive._vfs = vfs
    return archive


@pytest.mark.asyncio
async def test_yaml_task_archive_loads_task(tmp_path) -> None:
    (tmp_path / "task1.yaml").write_text(TASK_YAML)
    archive = make_task_archive(tmp_path)

    tasks = await archive.get_schedulable_tasks()
    assert len(tasks) == 1
    assert tasks[0].name == "Kochab"
    assert tasks[0].duration == 300


@pytest.mark.asyncio
async def test_yaml_task_archive_loads_target(tmp_path) -> None:
    (tmp_path / "task1.yaml").write_text(TASK_YAML)
    archive = make_task_archive(tmp_path)

    tasks = await archive.get_schedulable_tasks()
    assert isinstance(tasks[0].target, SiderealTarget)
    assert tasks[0].target.name == "Kochab"


@pytest.mark.asyncio
async def test_yaml_task_archive_empty_when_no_files(tmp_path) -> None:
    archive = make_task_archive(tmp_path)
    tasks = await archive.get_schedulable_tasks()
    assert tasks == []


@pytest.mark.asyncio
async def test_yaml_task_archive_get_task_by_id(tmp_path) -> None:
    (tmp_path / "task1.yaml").write_text(TASK_YAML)
    archive = make_task_archive(tmp_path)

    task = await archive.get_task("task1")
    assert task.name == "Kochab"


@pytest.mark.asyncio
async def test_yaml_task_archive_multiple_tasks(tmp_path) -> None:
    (tmp_path / "task1.yaml").write_text(TASK_YAML)
    (tmp_path / "task2.yaml").write_text(TASK_YAML.replace("Kochab", "Vega").replace("id: 1", "id: 2"))
    archive = make_task_archive(tmp_path)

    tasks = await archive.get_schedulable_tasks()
    assert len(tasks) == 2


@pytest.mark.asyncio
async def test_yaml_task_archive_last_changed_returns_none(tmp_path) -> None:
    archive = make_task_archive(tmp_path)
    result = await archive.last_changed()
    assert result is None
