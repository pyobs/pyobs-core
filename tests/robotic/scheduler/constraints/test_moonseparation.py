from __future__ import annotations

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation, SkyCoord

from pyobs.robotic import Task
from pyobs.robotic.scheduler.constraints import MoonSeparationConstraint
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.utils.time import Time


@pytest.mark.asyncio
async def test_moonseparation_constraint() -> None:
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    coord = SkyCoord("16h29m22.94s -26d25m53.0s", frame="icrs")
    task = Task(
        id=1,
        name="Antares",
        duration=100,
        target=SiderealTarget(ra=float(coord.ra.degree), dec=float(coord.dec.degree), name="Antares"),
    )

    constraint = MoonSeparationConstraint(min_distance=20.0)

    time = Time("2025-11-18T15:00:00", scale="utc")
    assert await constraint(time, task, data) is True

    time = Time("2025-11-19T11:00:00", scale="utc")
    assert await constraint(time, task, data) is True

    time = Time("2025-11-19T17:00:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-19T23:00:00", scale="utc")
    assert await constraint(time, task, data) is False


# ── filter_skycoord ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_moonseparation_filter_skycoord_passes_far() -> None:
    """filter_skycoord returns True for target far from moon."""
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    constraint = MoonSeparationConstraint(min_distance=20.0)

    coords = SkyCoord(["16h29m22.94s -26d25m53.0s"], frame="icrs")
    time = Time("2025-11-18T15:00:00", scale="utc")
    mask = await constraint.filter_skycoord(time, coords, data)
    assert bool(mask[0]) is True


@pytest.mark.asyncio
async def test_moonseparation_filter_skycoord_rejects_near() -> None:
    """filter_skycoord returns False for target too close to moon."""
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    constraint = MoonSeparationConstraint(min_distance=20.0)

    coords = SkyCoord(["16h29m22.94s -26d25m53.0s"], frame="icrs")
    time = Time("2025-11-19T23:00:00", scale="utc")
    mask = await constraint.filter_skycoord(time, coords, data)
    assert bool(mask[0]) is False


@pytest.mark.asyncio
async def test_moonseparation_filter_skycoord_agrees_with_call() -> None:
    """filter_skycoord result matches __call__ for each target."""
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    constraint = MoonSeparationConstraint(min_distance=20.0)
    time = Time("2025-11-19T23:00:00", scale="utc")

    # Antares (near moon at this time), Canopus (far)
    ras = [247.355, 95.988]
    decs = [-26.432, -52.691]
    coords = SkyCoord(ra=ras * u.deg, dec=decs * u.deg)

    mask = await constraint.filter_skycoord(time, coords, data)

    from pyobs.robotic import Task
    from pyobs.robotic.scheduler.targets import SiderealTarget

    for i, (ra, dec) in enumerate(zip(ras, decs)):
        task = Task(id=i, name="t", duration=100, target=SiderealTarget(ra=ra, dec=dec, name="t"))
        expected = await constraint(time, task, data)
        assert bool(mask[i]) == expected, f"Mismatch for target {i}"


@pytest.mark.asyncio
async def test_moonseparation_filter_skycoord_array_shape() -> None:
    """filter_skycoord returns correct shape and dtype for array input."""
    import numpy as np

    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    constraint = MoonSeparationConstraint(min_distance=30.0)
    time = Time("2025-11-03T23:00:00", scale="utc")

    coords = SkyCoord(ra=[0, 90, 180, 270] * u.deg, dec=[-30, -30, -30, -30] * u.deg)
    mask = await constraint.filter_skycoord(time, coords, data)

    assert mask.shape == (4,)
    assert mask.dtype == np.bool_
