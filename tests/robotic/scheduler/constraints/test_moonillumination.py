from __future__ import annotations

from unittest.mock import Mock

import astropy.units as u
import numpy as np
import pytest
from astroplan import FixedTarget, Observer
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.utils import iers

from pyobs.robotic import Task
from pyobs.robotic.scheduler.constraints import MoonIlluminationConstraint
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.utils.time import Time


@pytest.mark.asyncio
async def test_moonillumination_constraint() -> None:
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    task = Task(id=1, name="1", duration=100)
    constraint = MoonIlluminationConstraint(max_phase=0.5)

    time = Time("2025-11-05T13:00:00", scale="utc")
    assert await constraint(time, task, data) is True

    time = Time("2025-11-12T05:00:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-12T08:00:00", scale="utc")
    assert await constraint(time, task, data) is True

    time = Time("2025-11-13T0:00:00", scale="utc")
    assert await constraint(time, task, data) is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "altitude,illumination,max_phase,expected",
    [
        (-1.0, 1.0, 0.0, True),
        (-0.000001, 1.0, 0.0, True),
        (0.0, 0.2, 0.3, True),
        (0.0, 0.3, 0.3, True),
        (0.0, 0.4, 0.3, False),
        (10.0, 0.2, 0.3, True),
        (10.0, 0.3, 0.3, True),
        (10.0, 0.4, 0.3, False),
    ],
)
async def test_horizon_and_illumination_boundary(altitude, illumination, max_phase, expected):
    data = Mock(spec=DataProvider)
    data.moon_altaz.return_value.alt.degree = altitude
    data.moon_illumination.return_value = illumination
    time = Time("2026-10-18T22:00:00")
    task = Task(id=1, name="1", duration=100)

    result = await MoonIlluminationConstraint(max_phase=max_phase)(time, task, data)

    assert result is expected
    if altitude < 0.0:
        data.moon_illumination.assert_not_called()
    else:
        data.moon_illumination.assert_called_once_with(time)


@pytest.mark.asyncio
async def test_gottingen_moonset_matches_astroplan():
    observer = Observer(location=EarthLocation.from_geodetic(9.9445, 51.5606, 200.0))
    data = DataProvider(observer)
    task = Task(id=1, name="1", duration=100)
    target = FixedTarget(SkyCoord(ra=10.6847 * u.deg, dec=41.2687 * u.deg))
    constraint = MoonIlluminationConstraint(max_phase=0.30)
    cases = [
        ("2026-10-18T18:00:00", False),
        ("2026-10-18T20:00:00", False),
        ("2026-10-18T22:00:00", True),
        ("2026-10-19T00:00:00", True),
        ("2026-10-19T02:00:00", True),
    ]
    with iers.conf.set_temp("auto_download", False), iers.conf.set_temp("auto_max_age", None):
        for utc, expected in cases:
            time = Time(utc)
            assert await constraint(time, task, data) is expected
            assert bool(np.all(constraint.to_astroplan()(observer, target, times=time))) is expected
