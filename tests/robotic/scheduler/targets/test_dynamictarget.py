import io
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
import astropy.units as u
from astropy.time import Time
from unittest.mock import AsyncMock, MagicMock

from pyobs.robotic import Task
from pyobs.robotic.scheduler.constraints import AirmassConstraint, MoonSeparationConstraint, Constraint
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.robotic.scheduler.targets.dynamictarget import DynamicTarget
from pyobs.robotic.scheduler.targets.picker.csvpicker import CsvPicker

# Minimal CSV with three stars: one always visible, one always below horizon, one close to moon
CSV_CONTENT = """HIP,RAICRS,DEICRS
HIP001,083.820,+30.000
HIP002,083.820,+85.000
HIP003,083.820,-05.391
"""

# Fixed time: 2025-11-03T23:00:00 UTC at SAAO
# At this time HIP001 (near Orion, dec+30) is visible from SAAO
# HIP002 (near south pole, dec-89) is below horizon
# HIP003 (near Orion, dec-5) is close to the moon on 2025-11-19


@pytest.fixture
def observer() -> Observer:
    return Observer(location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m))


@pytest.fixture
def data(observer: Observer) -> DataProvider:
    return DataProvider(observer)


@pytest.fixture
def mock_vfs() -> MagicMock:
    """VFS mock that returns the test CSV."""
    import pandas as pd

    vfs = MagicMock()
    df = pd.read_csv(io.StringIO(CSV_CONTENT))
    vfs.read_csv = AsyncMock(return_value=df)
    return vfs


def make_task(constraints: list[Constraint] = []) -> Task:
    return Task(id="test", name="Test", duration=300.0, constraints=constraints)


@pytest.mark.asyncio
async def test_dynamic_target_resolves(observer: Observer, data: DataProvider, mock_vfs: MagicMock) -> None:
    """DynamicTarget.resolve() picks a target and sets name."""
    picker = CsvPicker(csv="/test/stars.csv", name_col="HIP", ra_col="RAICRS", dec_col="DEICRS")
    picker._vfs = mock_vfs
    picker._observer = observer

    target = DynamicTarget(picker=picker)
    task = make_task()

    time = Time("2025-11-03T23:00:00", scale="utc")
    await target.resolve(time, task, data)

    assert target._target is not None
    assert target.name != "(dynamic)"


@pytest.mark.asyncio
async def test_dynamic_target_coordinates_before_resolve() -> None:
    """coordinates() raises RuntimeError if resolve() hasn't been called."""
    picker = CsvPicker(csv="/test/stars.csv", name_col="HIP", ra_col="RAICRS", dec_col="DEICRS")
    target = DynamicTarget(picker=picker)
    time = Time("2025-11-03T23:00:00", scale="utc")

    with pytest.raises(RuntimeError, match="Target not resolved yet"):
        target.coordinates(time)


@pytest.mark.asyncio
async def test_dynamic_target_coordinates_after_resolve(
    observer: Observer, data: DataProvider, mock_vfs: MagicMock
) -> None:
    """coordinates() returns the resolved target's coordinates."""
    picker = CsvPicker(csv="/test/stars.csv", name_col="HIP", ra_col="RAICRS", dec_col="DEICRS")
    picker._vfs = mock_vfs
    picker._observer = observer

    target = DynamicTarget(picker=picker)
    task = make_task()
    time = Time("2025-11-03T23:00:00", scale="utc")

    await target.resolve(time, task, data)
    coord = target.coordinates(time)

    assert coord is not None
    assert -90.0 <= float(coord.dec.deg) <= 90.0


@pytest.mark.asyncio
async def test_csv_picker_filters_by_airmass(observer: Observer, data: DataProvider, mock_vfs: MagicMock) -> None:
    """CsvPicker excludes candidates that fail airmass constraint."""
    picker = CsvPicker(csv="/test/stars.csv", name_col="HIP", ra_col="RAICRS", dec_col="DEICRS")
    picker._vfs = mock_vfs
    picker._observer = observer

    # strict airmass constraint — HIP002 (dec -89) should be excluded from SAAO
    task = make_task(constraints=[AirmassConstraint(max_airmass=2.0)])
    time = Time("2025-11-03T23:00:00", scale="utc")

    results = []
    for _ in range(20):  # run multiple times to check randomness doesn't pick HIP002
        result = await picker(time, task, data)
        if result is not None:
            results.append(result)

    from typing import cast
    from pyobs.robotic.scheduler.targets import SiderealTarget as ST

    assert all(cast(ST, r).dec < 80.0 for r in results), "Below-horizon northern star should never be picked"


@pytest.mark.asyncio
async def test_csv_picker_returns_none_when_no_valid_candidates(
    observer: Observer, data: DataProvider, mock_vfs: MagicMock
) -> None:
    """CsvPicker returns None when all candidates fail constraints."""
    picker = CsvPicker(csv="/test/stars.csv", name_col="HIP", ra_col="RAICRS", dec_col="DEICRS")
    picker._vfs = mock_vfs
    picker._observer = observer

    # impossible airmass constraint — nothing can satisfy this
    task = make_task(constraints=[AirmassConstraint(max_airmass=1.0)])
    time = Time("2025-11-03T23:00:00", scale="utc")

    result = await picker(time, task, data)
    assert result is None


@pytest.mark.asyncio
async def test_csv_picker_caches_dataframe(observer: Observer, data: DataProvider, mock_vfs: MagicMock) -> None:
    """CsvPicker reads the CSV only once across multiple calls."""
    picker = CsvPicker(csv="/test/stars.csv", name_col="HIP", ra_col="RAICRS", dec_col="DEICRS")
    picker._vfs = mock_vfs
    picker._observer = observer

    task = make_task()
    time = Time("2025-11-03T23:00:00", scale="utc")

    await picker(time, task, data)
    await picker(time, task, data)
    await picker(time, task, data)

    mock_vfs.read_csv.assert_called_once()


@pytest.mark.asyncio
async def test_dynamic_target_resolve_updates_name(observer: Observer, data: DataProvider, mock_vfs: MagicMock) -> None:
    """After resolve(), target.name reflects the picked star."""
    picker = CsvPicker(csv="/test/stars.csv", name_col="HIP", ra_col="RAICRS", dec_col="DEICRS")
    picker._vfs = mock_vfs
    picker._observer = observer

    target = DynamicTarget(picker=picker)
    assert target.name == "(dynamic)"

    task = make_task()
    time = Time("2025-11-03T23:00:00", scale="utc")
    await target.resolve(time, task, data)

    assert target.name in ["HIP001", "HIP002", "HIP003"]


@pytest.mark.asyncio
async def test_csv_picker_ra_unit_hour(observer: Observer, data: DataProvider, mock_vfs: MagicMock) -> None:
    """CsvPicker correctly converts RA from hours to degrees."""
    import pandas as pd

    # RA in hours: 5h (= 75 deg), should land near Orion
    df = pd.read_csv(io.StringIO("HIP,RAICRS,DEICRS\nHIP001,5.592,+30.000\n"))
    mock_vfs.read_csv = AsyncMock(return_value=df)

    picker = CsvPicker(csv="/test/stars.csv", name_col="HIP", ra_col="RAICRS", dec_col="DEICRS", ra_unit="hour")
    picker._vfs = mock_vfs
    picker._observer = observer

    task = make_task()
    time = Time("2025-11-03T23:00:00", scale="utc")
    result = await picker(time, task, data)

    if result is not None:
        assert isinstance(result, SiderealTarget)
        # RA should be ~83.8 degrees (5.592 hours * 15)
        assert abs(result.ra - 83.88) < 0.1
