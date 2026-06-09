from __future__ import annotations

import astropy.units as u
import numpy as np
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation, SkyCoord

from pyobs.robotic import Task
from pyobs.robotic.scheduler.constraints import AirmassConstraint
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.utils.time import Time


@pytest.mark.asyncio
async def test_airmass_constraint() -> None:
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    coord = SkyCoord("6h23m58.2s -52d41m27.2s", frame="icrs")
    task = Task(
        id=1,
        name="Canopus",
        duration=100,
        target=SiderealTarget(ra=float(coord.ra.degree), dec=float(coord.dec.degree), name="Canopus"),
    )

    constraint = AirmassConstraint(max_airmass=1.3)

    time = Time("2025-11-03T17:00:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-03T19:00:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-03T21:00:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-03T23:00:00", scale="utc")
    assert await constraint(time, task, data) is True

    time = Time("2025-11-04T01:00:00", scale="utc")
    assert await constraint(time, task, data) is True


# ── filter_skycoord ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_airmass_filter_skycoord_passes_visible() -> None:
    """filter_skycoord returns True for Canopus at peak altitude."""
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    constraint = AirmassConstraint(max_airmass=1.3)

    # Canopus — passes at 23:00
    coords = SkyCoord(["6h23m58.2s -52d41m27.2s"], frame="icrs")
    time = Time("2025-11-03T23:00:00", scale="utc")
    mask = await constraint.filter_skycoord(time, coords, data)
    assert bool(mask[0]) is True


@pytest.mark.asyncio
async def test_airmass_filter_skycoord_rejects_below_horizon() -> None:
    """filter_skycoord returns False for target below horizon."""
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    constraint = AirmassConstraint(max_airmass=1.3)

    # Canopus — fails at 17:00 (below horizon)
    coords = SkyCoord(["6h23m58.2s -52d41m27.2s"], frame="icrs")
    time = Time("2025-11-03T17:00:00", scale="utc")
    mask = await constraint.filter_skycoord(time, coords, data)
    assert bool(mask[0]) is False


@pytest.mark.asyncio
async def test_airmass_filter_skycoord_agrees_with_call() -> None:
    """filter_skycoord result matches __call__ for each target."""
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    constraint = AirmassConstraint(max_airmass=1.3)
    time = Time("2025-11-03T23:00:00", scale="utc")

    # Canopus (passes), Polaris (fails at SAAO latitude)
    ras = [95.988, 37.954]
    decs = [-52.691, 89.264]
    coords = SkyCoord(ra=ras * u.deg, dec=decs * u.deg)

    mask = await constraint.filter_skycoord(time, coords, data)

    for i, (ra, dec) in enumerate(zip(ras, decs)):
        task = Task(id=i, name="t", duration=100, target=SiderealTarget(ra=ra, dec=dec, name="t"))
        expected = await constraint(time, task, data)
        assert bool(mask[i]) == expected, f"Mismatch for target {i}"


@pytest.mark.asyncio
async def test_airmass_filter_skycoord_array() -> None:
    """filter_skycoord returns correct shape for array input."""
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    constraint = AirmassConstraint(max_airmass=2.0)
    time = Time("2025-11-03T23:00:00", scale="utc")

    coords = SkyCoord(ra=[0, 90, 180, 270] * u.deg, dec=[-30, -30, -30, -30] * u.deg)
    mask = await constraint.filter_skycoord(time, coords, data)

    assert mask.shape == (4,)
    assert mask.dtype == np.bool_
