from __future__ import annotations

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.robotic import Task
from pyobs.robotic.scheduler.constraints import SolarElevationConstraint
from pyobs.robotic.scheduler.dataprovider import DataProvider
from pyobs.utils.time import Time


@pytest.mark.asyncio
async def test_solarelevation_constraint() -> None:
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    task = Task(id=1, name="1", duration=100)

    constraint = SolarElevationConstraint(max_elevation=-18.0)

    time = Time("2025-11-03T16:00:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-03T18:30:00", scale="utc")
    assert await constraint(time, task, data) is False

    time = Time("2025-11-03T18:35:00", scale="utc")
    assert await constraint(time, task, data) is True

    time = Time("2025-11-03T20:00:00", scale="utc")
    assert await constraint(time, task, data) is True


def test_solarelevation_has_no_direction() -> None:
    from pydantic import ValidationError

    assert "direction" not in SolarElevationConstraint.model_fields
    with pytest.raises(ValidationError):
        SolarElevationConstraint.model_validate({"max_elevation": -18.0, "direction": "rising"})


def test_solarelevation_limits_are_optional() -> None:
    c = SolarElevationConstraint()
    assert c.min_elevation is None
    assert c.max_elevation == -18.0
    assert SolarElevationConstraint(max_elevation=None).max_elevation is None


def test_solarelevation_unbounded_values_normalised() -> None:
    c = SolarElevationConstraint(min_elevation=-90, max_elevation=90)
    assert c.min_elevation is None
    assert c.max_elevation is None
    assert c.req_fields() == {}


def test_solarelevation_schema_is_nullable() -> None:
    props = SolarElevationConstraint.model_json_schema()["properties"]
    for field in ("min_elevation", "max_elevation"):
        assert {"type": "null"} in props[field]["anyOf"]
        assert props[field]["x-pyobs-stricter"] in ("lower", "higher")


@pytest.mark.asyncio
async def test_solarelevation_min_only() -> None:
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    task = Task(id=1, name="1", duration=100)

    # sun above -10 deg: daytime/twilight passes, night fails
    constraint = SolarElevationConstraint(min_elevation=-10.0, max_elevation=None)
    assert await constraint(Time("2025-11-03T16:00:00", scale="utc"), task, data) is True
    assert await constraint(Time("2025-11-03T20:00:00", scale="utc"), task, data) is False
