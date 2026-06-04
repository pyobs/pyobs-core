import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import Time
import astropy.units as u

from pyobs.robotic import Task
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.constraints import SolarElevationConstraint

# SAAO, 2025-11-03:
# Sun passes -18deg going DOWN (setting) at ~18:34:36 UTC
# Sun passes -18deg going UP   (rising)  at ~02:06:50 UTC
# Sun is SETTING  between ~18:29 and ~18:39 UTC (alt between -17 and -19)
# Sun is RISING   between ~02:01 and ~02:11 UTC (alt between -19 and -17)
# Solar midnight (nadir) is at approximately 2025-11-03 12:20 UTC (local noon + offset)


@pytest.fixture
def observer() -> Observer:
    return Observer(location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m))


@pytest.fixture
def data(observer: Observer) -> DataProvider:
    return DataProvider(observer)


@pytest.fixture
def task() -> Task:
    return Task(id=1, name="test", duration=100)


@pytest.fixture
def constraint() -> SolarElevationConstraint:
    return SolarElevationConstraint(min_elevation=-19.0, max_elevation=-17.0)


# ── direction="both" ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_both_passes_during_setting(task: Task, data: DataProvider, constraint: SolarElevationConstraint) -> None:
    """direction=both: passes when sun is in range regardless of direction."""
    time = Time("2025-11-03T18:32:00", scale="utc")  # setting, alt ~ -17.5
    constraint.direction = "both"
    assert await constraint(time, task, data) is True


@pytest.mark.asyncio
async def test_both_passes_during_rising(task: Task, data: DataProvider, constraint: SolarElevationConstraint) -> None:
    """direction=both: passes when sun is in range on the way up."""
    time = Time("2025-11-03T02:04:00", scale="utc")  # rising, alt ~ -18.5
    constraint.direction = "both"
    assert await constraint(time, task, data) is True


@pytest.mark.asyncio
async def test_both_fails_outside_range(task: Task, data: DataProvider, constraint: SolarElevationConstraint) -> None:
    """direction=both: fails when sun is outside elevation range."""
    time = Time("2025-11-03T20:00:00", scale="utc")  # deep night
    constraint.direction = "both"
    assert await constraint(time, task, data) is False


# ── direction="setting" ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_setting_passes_when_sun_setting_in_range(
    task: Task, data: DataProvider, constraint: SolarElevationConstraint
) -> None:
    """direction=setting: passes when sun is in range and moving downward."""
    time = Time("2025-11-03T18:32:00", scale="utc")  # setting, alt ~ -17.5
    constraint.direction = "setting"
    assert await constraint(time, task, data) is True


@pytest.mark.asyncio
async def test_setting_fails_when_sun_rising_in_range(
    task: Task, data: DataProvider, constraint: SolarElevationConstraint
) -> None:
    """direction=setting: fails when sun is in range but moving upward."""
    time = Time("2025-11-03T02:04:00", scale="utc")  # rising, alt ~ -18.5
    constraint.direction = "setting"
    assert await constraint(time, task, data) is False


@pytest.mark.asyncio
async def test_setting_fails_outside_range(
    task: Task, data: DataProvider, constraint: SolarElevationConstraint
) -> None:
    """direction=setting: fails when sun is outside elevation range."""
    time = Time("2025-11-03T20:00:00", scale="utc")  # deep night
    constraint.direction = "setting"
    assert await constraint(time, task, data) is False


# ── direction="rising" ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rising_passes_when_sun_rising_in_range(
    task: Task, data: DataProvider, constraint: SolarElevationConstraint
) -> None:
    """direction=rising: passes when sun is in range and moving upward."""
    time = Time("2025-11-03T02:04:00", scale="utc")  # rising, alt ~ -18.5
    constraint.direction = "rising"
    assert await constraint(time, task, data) is True


@pytest.mark.asyncio
async def test_rising_fails_when_sun_setting_in_range(
    task: Task, data: DataProvider, constraint: SolarElevationConstraint
) -> None:
    """direction=rising: fails when sun is in range but moving downward."""
    time = Time("2025-11-03T18:32:00", scale="utc")  # setting, alt ~ -17.5
    constraint.direction = "rising"
    assert await constraint(time, task, data) is False


@pytest.mark.asyncio
async def test_rising_fails_outside_range(task: Task, data: DataProvider, constraint: SolarElevationConstraint) -> None:
    """direction=rising: fails when sun is outside elevation range."""
    time = Time("2025-11-03T20:00:00", scale="utc")  # deep night
    constraint.direction = "rising"
    assert await constraint(time, task, data) is False
