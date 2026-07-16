from __future__ import annotations

import warnings

import astropy.units as u
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.utils.time import Time

# a mid-latitude site, where the sun rises and sets every day
MID_LATITUDE_LOCATION = EarthLocation.from_geodetic(lon=10 * u.deg, lat=50 * u.deg, height=500 * u.m)

# a site above the Arctic circle, which experiences polar day/night
POLAR_LOCATION = EarthLocation.from_geodetic(lon=10 * u.deg, lat=70 * u.deg, height=500 * u.m)


def test_night_obs_uses_sunset_date() -> None:
    observer = Observer(location=MID_LATITUDE_LOCATION, timezone="UTC")
    t = Time("2026-07-16T15:45:50")
    assert t.night_obs(observer) == t.to_datetime().date()


def test_night_obs_falls_back_to_local_date_during_polar_day() -> None:
    observer = Observer(location=POLAR_LOCATION, timezone="UTC")
    t = Time("2026-07-16T15:45:50")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        night = t.night_obs(observer)

    assert night == t.to_datetime(timezone=observer.timezone).date()
