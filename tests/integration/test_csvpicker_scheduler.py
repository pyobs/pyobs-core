from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import TimeDelta

from pyobs.robotic import Task
from pyobs.robotic.observation import ObservationList, ObservationState
from pyobs.robotic.scheduler.constraints import AirmassConstraint
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.merits import ConstantMerit
from pyobs.robotic.scheduler.ondemandscheduler import OnDemandScheduler
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.robotic.scheduler.targets.dynamictarget import DynamicTarget
from pyobs.robotic.scheduler.targets.picker.csvpicker import CsvPicker
from pyobs.vfs.vfs import VirtualFileSystem
from tests.integration.test_mastermind import (
    NIGHT,
    make_mastermind,
    run_until_state,
)
from tests.integration.test_scheduler_mastermind import make_obs_archive

SAAO = Observer(location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m))

WINDOW_END = NIGHT + TimeDelta(2 * 3600 * u.second)

# Stars visible from SAAO on 2025-11-03 night
CSV_VISIBLE = """name,ra,dec
Betelgeuse,83.82,7.41
Rigel,78.63,-8.20
Sirius,101.29,-16.72
"""

# Stars never visible from SAAO (far north)
CSV_INVISIBLE = """name,ra,dec
Polaris,37.95,89.26
Kochab,222.68,74.16
"""


def make_vfs(tmp_path: Path, csv_content: str, filename: str = "catalogue.csv") -> tuple[VirtualFileSystem, str]:
    """Write CSV to tmp_path and return a VFS + path string."""
    csv_path = tmp_path / filename
    csv_path.write_text(csv_content)
    vfs = VirtualFileSystem(roots={"test": {"class": "pyobs.vfs.LocalFile", "root": str(tmp_path) + "/"}})
    return vfs, f"test/{filename}"


def make_dynamic_task(vfs: VirtualFileSystem, csv_path: str, constraints: list | None = None) -> Task:
    picker = CsvPicker(csv=csv_path, name_col="name", ra_col="ra", dec_col="dec")
    picker._vfs = vfs
    picker._observer = SAAO
    target = DynamicTarget(picker=picker)
    target._observer = SAAO
    target._vfs = vfs
    return Task(
        id=1,
        name="csv_task",
        duration=300,
        target=target,
        merits=[ConstantMerit(merit=1.0)],
        constraints=constraints or [],
    )


# ── CsvPicker + DataProvider ──────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_csvpicker_picks_visible_target(tmp_path: Path) -> None:
    """CsvPicker returns a SiderealTarget from the CSV catalogue."""
    vfs, csv_path = make_vfs(tmp_path, CSV_VISIBLE)
    task = make_dynamic_task(vfs, csv_path)
    data = DataProvider(SAAO)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        await task.resolve_target(NIGHT, task, data)
        result = task._resolved_target

    assert result is not None
    assert isinstance(result, SiderealTarget)
    assert result.name in ["Betelgeuse", "Rigel", "Sirius"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_csvpicker_returns_none_for_invisible_targets(tmp_path: Path) -> None:
    """CsvPicker returns None when all targets fail the airmass constraint."""
    vfs, csv_path = make_vfs(tmp_path, CSV_INVISIBLE)
    task = make_dynamic_task(vfs, csv_path, constraints=[AirmassConstraint(max_airmass=2.0)])
    data = DataProvider(SAAO)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        await task.resolve_target(NIGHT, task, data)
        result = task._resolved_target

    assert result is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_csvpicker_respects_airmass_constraint(tmp_path: Path) -> None:
    """CsvPicker filters out targets that fail the airmass constraint."""
    # Mix visible and invisible targets
    mixed_csv = CSV_VISIBLE + "Polaris,37.95,89.26\n"
    vfs, csv_path = make_vfs(tmp_path, mixed_csv)
    task = make_dynamic_task(vfs, csv_path, constraints=[AirmassConstraint(max_airmass=2.0)])
    data = DataProvider(SAAO)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        await task.resolve_target(NIGHT, task, data)
        result = task._resolved_target

    assert result is not None
    assert result.name != "Polaris"


# ── CsvPicker + OnDemandScheduler ─────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scheduler_resolves_csv_dynamic_target(tmp_path: Path) -> None:
    """OnDemandScheduler resolves DynamicTarget via CsvPicker to a SiderealTarget."""
    vfs, csv_path = make_vfs(tmp_path, CSV_VISIBLE)
    task = make_dynamic_task(vfs, csv_path)

    scheduler = OnDemandScheduler()
    data = DataProvider(SAAO)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        observations = ObservationList()
        async for obs in scheduler.schedule_in_interval([task], {}, NIGHT, WINDOW_END, data):
            observations.append(obs)

    assert len(observations) >= 1
    assert isinstance(observations[0].task._resolved_target, SiderealTarget)
    assert observations[0].task._resolved_target.name in ["Betelgeuse", "Rigel", "Sirius"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scheduler_skips_csv_task_with_no_visible_target(tmp_path: Path) -> None:
    """Scheduler produces no observations when all CSV targets are invisible."""
    vfs, csv_path = make_vfs(tmp_path, CSV_INVISIBLE)
    task = make_dynamic_task(vfs, csv_path, constraints=[AirmassConstraint(max_airmass=2.0)])

    scheduler = OnDemandScheduler()
    data = DataProvider(SAAO)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        observations = ObservationList()
        async for obs in scheduler.schedule_in_interval([task], {}, NIGHT, WINDOW_END, data):
            observations.append(obs)

    assert len(observations) == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_resolved_target_preserved_in_observation(tmp_path: Path) -> None:
    """The resolved SiderealTarget is stored on the observation."""
    vfs, csv_path = make_vfs(tmp_path, CSV_VISIBLE)
    task = make_dynamic_task(vfs, csv_path)

    scheduler = OnDemandScheduler()
    data = DataProvider(SAAO)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        observations = ObservationList()
        async for obs in scheduler.schedule_in_interval([task], {}, NIGHT, WINDOW_END, data):
            observations.append(obs)

    assert len(observations) >= 1
    assert isinstance(observations[0].target, SiderealTarget)
    assert observations[0].target.name in ["Betelgeuse", "Rigel", "Sirius"]


# ── scheduler → mastermind pipeline ──────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_csv_scheduler_to_mastermind_completes_task(tmp_path: Path) -> None:
    """Full pipeline: CsvPicker → Scheduler → Mastermind completes task."""
    vfs, csv_path = make_vfs(tmp_path, CSV_VISIBLE)
    task = make_dynamic_task(vfs, csv_path)

    scheduler = OnDemandScheduler()
    data = DataProvider(SAAO)

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        observations = ObservationList()
        async for obs in scheduler.schedule_in_interval([task], {}, NIGHT, WINDOW_END, data):
            observations.append(obs)
            break  # just need one

    assert len(observations) >= 1

    obs_archive = make_obs_archive()
    await obs_archive.add_observations(ObservationList([observations[0]]))

    mm = make_mastermind(obs_archive)
    reached = await run_until_state(mm, obs_archive, ObservationState.COMPLETED, timeout=15.0)
    assert reached, "Mastermind did not complete the CSV-scheduled observation"
