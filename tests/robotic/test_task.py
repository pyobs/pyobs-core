from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
import yaml

from pyobs.robotic import Task
from pyobs.robotic.observation import Observation
from pyobs.robotic.scheduler.constraints import AirmassConstraint
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.robotic.scripts import Script
from pyobs.robotic.task import TaskData
from pyobs.utils.time import Time

# ── module-level script stubs (needed so pyobs_model_validate can find them) ─


class _TimedScript(Script):
    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        return 42.0


class _AlwaysCanRunScript(Script):
    async def can_run(self, data: TaskData | None) -> bool:
        return True


class _NeverCanRunScript(Script):
    async def can_run(self, data: TaskData | None) -> bool:
        return False


# ── helpers ──────────────────────────────────────────────────────────────────


def _blank_context(task: Task) -> Task:
    """Set private attrs to None so pyobs_model_validate works without Object."""
    task._comm = None
    task._observer = None
    task._vfs = None
    task._timezone = None
    task._location = None
    return task


# ── YAML parsing ─────────────────────────────────────────────────────────────

TASK_CONFIG = """
---
class: pyobs.robotic.Task
id: kochab
name: Kochab
priority: 1
duration: 2253
constraints:
  - class: pyobs.robotic.scheduler.constraints.AirmassConstraint
    max_airmass: 1.3
  - class: pyobs.robotic.scheduler.constraints.MoonSeparationConstraint
    min_distance: 30.0
merits:
  - class: pyobs.robotic.scheduler.merits.PerNightMerit
    count: 3
target:
  class: pyobs.robotic.scheduler.targets.SiderealTarget
  name: Kochab
  ra: 222.6763575
  dec: 74.1555039444
script:
  class: pyobs.robotic.scripts.Script
"""


def test_create_task() -> None:
    task_config = yaml.safe_load(TASK_CONFIG)
    task = Task.model_validate(task_config)

    assert task.name == "Kochab"
    assert len(task.constraints) == 2
    constraint = task.constraints[0]
    assert isinstance(constraint, AirmassConstraint)
    assert constraint.max_airmass == 1.3


# ── can_start_late ────────────────────────────────────────────────────────────


def test_can_start_late_is_false_by_default() -> None:
    task = Task(id=1, name="test", duration=100)
    assert task.can_start_late is False


# ── estimate_duration ─────────────────────────────────────────────────────────


def test_estimate_duration_falls_back_to_duration() -> None:
    task = Task(id=1, name="test", duration=300.0)
    assert task.estimate_duration() == 300.0


def test_estimate_duration_delegates_to_script() -> None:
    task = _blank_context(
        Task(
            id=1,
            name="test",
            duration=300.0,
            script={"class": "tests.robotic.test_task._TimedScript"},
        )
    )
    assert task.estimate_duration() == 42.0


# ── can_run ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_can_run_returns_true_when_no_script() -> None:
    task = Task(id=1, name="test", duration=100)
    assert await task.can_run(None) is True


@pytest.mark.asyncio
async def test_can_run_delegates_to_script() -> None:
    for cls, expected in [(_AlwaysCanRunScript, True), (_NeverCanRunScript, False)]:
        task = _blank_context(
            Task(
                id=1,
                name="test",
                duration=100,
                script={"class": f"tests.robotic.test_task.{cls.__name__}"},
            )
        )
        assert await task.can_run(None) is expected


# ── target property + set_resolved_target ─────────────────────────────────────


def test_set_resolved_target() -> None:
    task = Task(id=1, name="test", duration=100)
    target = SiderealTarget(name="Vega", ra=279.23, dec=38.78)

    task.set_resolved_target(target)
    assert task.target is target

    # second call should not overwrite
    task.set_resolved_target(SiderealTarget(name="Sirius", ra=101.28, dec=-16.72))
    assert task.target.name == "Vega"


def test_task_target_property_falls_back_to_static() -> None:
    task = Task(id=1, name="test", duration=100, target=SiderealTarget(name="Vega", ra=279.23, dec=38.78))
    assert task.target.name == "Vega"

    task.set_resolved_target(SiderealTarget(name="Sirius", ra=101.28, dec=-16.72))
    assert task.target.name == "Sirius"


# ── fetch_task ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_task_restores_resolved_target() -> None:
    sidereal = SiderealTarget(name="Vega", ra=279.23, dec=38.78)
    task = Task(id=1, name="test", duration=100)
    obs = Observation(task=1, start=Time.now(), end=Time.now(), target=sidereal)

    mock_archive = AsyncMock()
    mock_archive.get_task = AsyncMock(return_value=task)

    await obs.fetch_task(mock_archive)
    assert obs.task.target is not None
    assert obs.task.target.name == "Vega"


# ── resolve_target ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resolve_target_caches_result() -> None:
    import astropy.units as u
    from astroplan import Observer
    from astropy.coordinates import EarthLocation

    from pyobs.robotic.scheduler.dataprovider import DataProvider
    from pyobs.robotic.scheduler.targets.dynamictarget import DynamicTarget
    from pyobs.robotic.scheduler.targets.picker.picker import Picker

    call_count = 0

    class CountingPicker(Picker):
        async def __call__(self, time, task, data):
            nonlocal call_count
            call_count += 1
            return SiderealTarget(name="Vega", ra=279.23, dec=38.78)

    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    time = Time("2025-11-03T23:00:00", scale="utc")

    task = Task(id=1, name="test", duration=100, target=DynamicTarget(picker=CountingPicker()))

    await task.resolve_target(time, task, data)
    await task.resolve_target(time, task, data)
    await task.resolve_target(time, task, data)

    assert call_count == 1
    assert task.target.name == "Vega"


@pytest.mark.asyncio
async def test_resolve_target_returns_false_when_no_candidate() -> None:
    import astropy.units as u
    from astroplan import Observer
    from astropy.coordinates import EarthLocation

    from pyobs.robotic.scheduler.dataprovider import DataProvider
    from pyobs.robotic.scheduler.targets.dynamictarget import DynamicTarget
    from pyobs.robotic.scheduler.targets.picker.picker import Picker

    class EmptyPicker(Picker):
        async def __call__(self, time, task, data):
            return None

    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    time = Time("2025-11-03T23:00:00", scale="utc")

    task = Task(id=1, name="test", duration=100, target=DynamicTarget(picker=EmptyPicker()))

    result = await task.resolve_target(time, task, data)
    assert result is False
    # static_target is DynamicTarget, _resolved_target is None,
    # so target property returns the DynamicTarget (not None)
    assert task._resolved_target is None
