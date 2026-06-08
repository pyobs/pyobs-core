from __future__ import annotations

import asyncio
import io
from unittest.mock import AsyncMock, MagicMock

import astropy.units as u
import pandas as pd
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import TimeDelta

from pyobs.robotic import Task
from pyobs.robotic.memory import MemoryTaskArchive
from pyobs.robotic.observation import ObservationList, ObservationState
from pyobs.robotic.scheduler.constraints import AirmassConstraint
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits import ConstantMerit
from pyobs.robotic.scheduler.ondemandscheduler import OnDemandScheduler
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.robotic.scheduler.targets.dynamictarget import DynamicTarget
from pyobs.robotic.scheduler.targets.picker.csvpicker import CsvPicker
from tests.integration.test_mastermind import (
    NIGHT,
    QuickRunner,
    make_mastermind,
    make_obs_archive,
    run_until_state,
)

SAAO = Observer(location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m))


# ── CSV catalogue with two targets ───────────────────────────────────────────
# Betelgeuse is well-placed from SAAO on 2025-11-03 night
# A polar target at dec=+85 is never visible

CSV_CONTENT = """HIP,RAICRS,DEICRS
Betelgeuse,083.820,+07.407
PolarStar,083.820,+85.000
"""


def make_mock_vfs(csv_content: str = CSV_CONTENT) -> MagicMock:
    vfs = MagicMock()
    df = pd.read_csv(io.StringIO(csv_content))
    vfs.read_csv = AsyncMock(return_value=df)
    return vfs


def make_dynamic_task(vfs: MagicMock) -> Task:
    picker = CsvPicker(csv="/test/stars.csv", name_col="HIP", ra_col="RAICRS", dec_col="DEICRS")
    picker._vfs = vfs
    picker._observer = SAAO
    target = DynamicTarget(picker=picker)
    target._observer = SAAO
    target._vfs = vfs
    return Task(
        id=1,
        name="dynamic_task",
        duration=300,
        target=target,
        merits=[ConstantMerit(merit=1.0)],
    )


# ── scheduler + dynamic target ────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scheduler_resolves_dynamic_target() -> None:
    """OnDemandScheduler resolves a DynamicTarget to a concrete SiderealTarget."""
    vfs = make_mock_vfs()
    task = make_dynamic_task(vfs)

    scheduler = OnDemandScheduler()
    data = DataProvider(SAAO)
    end = NIGHT + TimeDelta(3600 * u.second)

    best, merit = await scheduler.find_next_best_task([task], {}, NIGHT, end, data)

    assert best is not None
    assert merit > 0.0
    assert task._resolved_target is not None
    assert isinstance(task._resolved_target, SiderealTarget)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scheduler_picks_visible_target_only() -> None:
    """Scheduler only picks targets that pass constraints — the polar target fails airmass."""
    csv = """HIP,RAICRS,DEICRS
PolarStar,083.820,+85.000
"""
    vfs = make_mock_vfs(csv)
    picker = CsvPicker(csv="/test/stars.csv", name_col="HIP", ra_col="RAICRS", dec_col="DEICRS")
    picker._vfs = vfs
    picker._observer = SAAO
    target = DynamicTarget(picker=picker)
    target._observer = SAAO
    target._vfs = vfs
    task = Task(
        id=1,
        name="polar_task",
        duration=300,
        target=target,
        constraints=[AirmassConstraint(max_airmass=2.0)],
        merits=[ConstantMerit(merit=1.0)],
    )

    scheduler = OnDemandScheduler()
    data = DataProvider(SAAO)
    end = NIGHT + TimeDelta(3600 * u.second)

    best, merit = await scheduler.find_next_best_task([task], {}, NIGHT, end, data)

    assert best is None or merit == 0.0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_observation_carries_resolved_target() -> None:
    """Observation created after scheduling carries the resolved SiderealTarget."""
    vfs = make_mock_vfs()
    task = make_dynamic_task(vfs)

    scheduler = OnDemandScheduler()
    data = DataProvider(SAAO)
    end = NIGHT + TimeDelta(3600 * u.second)

    best, merit = await scheduler.find_next_best_task([task], {}, NIGHT, end, data)
    assert best is not None

    obs = scheduler.create_scheduled_task(best, merit, NIGHT)
    assert obs is not None
    assert isinstance(obs.target, SiderealTarget)
    assert obs.target.name in ["Betelgeuse", "PolarStar"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_receives_resolved_target() -> None:
    """After scheduling, the observation carries the resolved SiderealTarget.
    fetch_task restores it on the task when the mastermind loads from the archive."""
    vfs = make_mock_vfs()
    task = make_dynamic_task(vfs)

    # schedule to get a concrete observation with resolved target
    scheduler = OnDemandScheduler()
    data = DataProvider(SAAO)
    end = NIGHT + TimeDelta(3600 * u.second)

    best, merit = await scheduler.find_next_best_task([task], {}, NIGHT, end, data)
    assert best is not None
    obs = scheduler.create_scheduled_task(best, merit, NIGHT)
    assert obs is not None
    resolved_name = obs.target.name

    # store in archive
    obs_archive = make_obs_archive()
    await obs_archive.add_observations(ObservationList([obs]))

    # task archive so fetch_task can restore the resolved target
    task_archive = MemoryTaskArchive([task])

    # track what target the runner sees
    seen_targets = []

    class TrackingRunner(QuickRunner):
        async def run_task(self, t) -> bool:
            seen_targets.append(t.target)
            await asyncio.sleep(0.05)
            return True

    mm = make_mastermind(obs_archive, runner=TrackingRunner())
    mm._task_archive = task_archive
    reached = await run_until_state(mm, obs_archive, ObservationState.COMPLETED)

    assert reached, "Observation did not complete"
    assert len(seen_targets) == 1
    assert isinstance(seen_targets[0], SiderealTarget), f"Expected SiderealTarget, got {type(seen_targets[0])}"
    assert seen_targets[0].name == resolved_name


@pytest.mark.asyncio
@pytest.mark.integration
async def test_target_consistent_across_scheduling_run() -> None:
    """The same target is returned consistently within a single scheduling run."""
    vfs = make_mock_vfs()
    task = make_dynamic_task(vfs)

    scheduler = OnDemandScheduler()
    data = DataProvider(SAAO)
    end = NIGHT + TimeDelta(3600 * u.second)

    # resolve once
    await scheduler.evaluate_constraints_and_merits([task], {}, NIGHT, end, data)
    first_target = task._resolved_target

    # resolve again — should return same cached result
    await scheduler.evaluate_constraints_and_merits([task], {}, NIGHT, end, data)
    second_target = task._resolved_target

    assert first_target is not None
    assert second_target is not None
    assert first_target.name == second_target.name
