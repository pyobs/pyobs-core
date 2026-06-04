import io
import pytest
import pandas as pd
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import TimeDelta
import astropy.units as u
from unittest.mock import AsyncMock, MagicMock

from pyobs.robotic import Task
from pyobs.robotic.observation import Observation
from pyobs.robotic.scheduler import DataProvider
from pyobs.robotic.scheduler.constraints import AirmassConstraint
from pyobs.robotic.scheduler.merits import ConstantMerit
from pyobs.robotic.scheduler.ondemandscheduler import OnDemandScheduler
from pyobs.robotic.scheduler.targets.dynamictarget import DynamicTarget
from pyobs.robotic.scheduler.targets.picker.csvpicker import CsvPicker
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.utils.time import Time

# One star well-placed from SAAO at night, one permanently below horizon (dec > +80)
CSV_CONTENT = """HIP,RAICRS,DEICRS
HIP001,083.820,+30.000
HIP002,083.820,+85.000
"""


@pytest.fixture
def observer() -> Observer:
    return Observer(location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m))


@pytest.fixture
def mock_vfs() -> MagicMock:
    vfs = MagicMock()
    df = pd.read_csv(io.StringIO(CSV_CONTENT))
    vfs.read_csv = AsyncMock(return_value=df)
    return vfs


def make_dynamic_task(mock_vfs: MagicMock, observer: Observer, constraints: list = []) -> Task:
    picker = CsvPicker(csv="/test/stars.csv", name_col="HIP", ra_col="RAICRS", dec_col="DEICRS")
    picker._vfs = mock_vfs
    picker._observer = observer
    target = DynamicTarget(picker=picker)
    target._observer = observer
    target._vfs = mock_vfs
    return Task(
        id=1,
        name="dynamic",
        duration=300,
        target=target,
        merits=[ConstantMerit(merit=5.0)],
        constraints=constraints,
    )


@pytest.mark.asyncio
async def test_dynamic_target_scheduled(observer: Observer, mock_vfs: MagicMock) -> None:
    """Scheduler picks a task with DynamicTarget and resolves a concrete target."""
    scheduler = OnDemandScheduler()
    data = DataProvider(observer)
    start = Time("2025-11-03T23:00:00", scale="utc")
    end = start + TimeDelta(3600 * u.second)

    task = make_dynamic_task(mock_vfs, observer)
    best, merit = await scheduler.find_next_best_task([task], {}, start, end, data)

    assert best is not None
    assert merit > 0.0
    # target should now be resolved on the task
    assert task._resolved_target is not None
    assert isinstance(task._resolved_target, SiderealTarget)


@pytest.mark.asyncio
async def test_dynamic_target_observation_carries_target(observer: Observer, mock_vfs: MagicMock) -> None:
    """Observation created from a DynamicTarget task has a concrete resolved target."""
    scheduler = OnDemandScheduler()
    data = DataProvider(observer)
    start = Time("2025-11-03T23:00:00", scale="utc")
    end = start + TimeDelta(3600 * u.second)

    task = make_dynamic_task(mock_vfs, observer)

    # resolve first via scheduling, then create observation
    await scheduler.find_next_best_task([task], {}, start, end, data)
    obs = scheduler.create_scheduled_task(task, 5.0, start)

    assert obs is not None
    assert obs.target is not None
    assert isinstance(obs.target, SiderealTarget)
    assert obs.target.name in ["HIP001", "HIP002"]


@pytest.mark.asyncio
async def test_dynamic_target_constraint_excludes_bad_target(observer: Observer, mock_vfs: MagicMock) -> None:
    """Task with DynamicTarget gets merit 0 when all candidates fail constraints."""
    scheduler = OnDemandScheduler()
    data = DataProvider(observer)
    start = Time("2025-11-03T23:00:00", scale="utc")
    end = start + TimeDelta(3600 * u.second)

    # impossible airmass — nothing will pass
    task = make_dynamic_task(mock_vfs, observer, constraints=[AirmassConstraint(max_airmass=1.0)])
    merits = await scheduler.evaluate_constraints_and_merits([task], {}, start, end, data)

    assert merits[0] == 0.0


@pytest.mark.asyncio
async def test_dynamic_target_same_target_throughout_scheduling(observer: Observer, mock_vfs: MagicMock) -> None:
    """The same resolved target is used consistently across the scheduling run."""
    scheduler = OnDemandScheduler()
    data = DataProvider(observer)
    start = Time("2025-11-03T23:00:00", scale="utc")
    end = start + TimeDelta(3600 * u.second)

    task = make_dynamic_task(mock_vfs, observer)

    # evaluate multiple times — target should be the same each time
    await scheduler.evaluate_constraints_and_merits([task], {}, start, end, data)
    first_target = task._resolved_target

    await scheduler.evaluate_constraints_and_merits([task], {}, start, end, data)
    second_target = task._resolved_target

    assert first_target is not None
    assert second_target is not None
    assert first_target.name == second_target.name


@pytest.mark.asyncio
async def test_static_target_unaffected(observer: Observer) -> None:
    """Tasks with SiderealTarget still work correctly — resolve is a no-op."""
    scheduler = OnDemandScheduler()
    data = DataProvider(observer)
    start = Time("2025-11-03T23:00:00", scale="utc")
    end = start + TimeDelta(3600 * u.second)

    task = Task(
        id=2,
        name="static",
        duration=300,
        target=SiderealTarget(name="Betelgeuse", ra=83.82, dec=7.41),
        merits=[ConstantMerit(merit=3.0)],
    )
    best, merit = await scheduler.find_next_best_task([task], {}, start, end, data)

    assert best is not None
    assert merit == 3.0
    assert task._resolved_target is not None
    assert task._resolved_target.name == "Betelgeuse"
