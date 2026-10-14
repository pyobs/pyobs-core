"""FITS header cards of the constraints (`HIERARCH REQ ...`, #962)."""

from __future__ import annotations

import warnings
from typing import ClassVar

import astropy.units as u
import pytest
from astropy.io import fits

from pyobs.interfaces import FitsHeaderEntry
from pyobs.robotic.scheduler.constraints import (
    AirmassConstraint,
    MoonIlluminationConstraint,
    MoonSeparationConstraint,
    SolarElevationConstraint,
    TimeConstraint,
)
from pyobs.robotic.scheduler.constraints.constraint import Constraint
from pyobs.utils.time import Time


def values(headers: dict[str, FitsHeaderEntry]) -> dict[str, object]:
    return {k: v.value for k, v in headers.items()}


def test_airmass() -> None:
    assert values(AirmassConstraint(max_airmass=1.5).get_fits_headers(1)) == {"HIERARCH REQ AIRMASS MAX": 1.5}


def test_moon_separation() -> None:
    assert values(MoonSeparationConstraint(min_distance=25.0).get_fits_headers(1)) == {
        "HIERARCH REQ MOONDIST MIN": 25.0
    }


def test_moon_illumination() -> None:
    assert values(MoonIlluminationConstraint(max_phase=0.4).get_fits_headers(1)) == {"HIERARCH REQ MOONFRAC MAX": 0.4}


def test_solar_elevation_omits_unbounded_default() -> None:
    assert values(SolarElevationConstraint().get_fits_headers(1)) == {
        "HIERARCH REQ SUNALT MAX": -18.0,
        "HIERARCH REQ SUNALT DIR": "both",
    }


@pytest.mark.parametrize(
    ("minimum", "maximum", "expected_bounds"),
    [
        (-90.0, 90.0, {}),
        (-90.0, 89.0, {"MAX": 89.0}),
        (-89.0, 90.0, {"MIN": -89.0}),
        (-89.0, 89.0, {"MIN": -89.0, "MAX": 89.0}),
    ],
)
def test_solar_elevation_only_writes_effective_bounds(
    minimum: float, maximum: float, expected_bounds: dict[str, float]
) -> None:
    constraint = SolarElevationConstraint(min_elevation=minimum, max_elevation=maximum, direction="rising")
    expected: dict[str, object] = {f"HIERARCH REQ SUNALT2 {name}": value for name, value in expected_bounds.items()}
    expected["HIERARCH REQ SUNALT2 DIR"] = "rising"
    assert values(constraint.get_fits_headers(2)) == expected


def test_solar_elevation_with_values() -> None:
    constraint = SolarElevationConstraint(min_elevation=-30.0, max_elevation=-12.0, direction="setting")
    assert values(constraint.get_fits_headers(1)) == {
        "HIERARCH REQ SUNALT MIN": -30.0,
        "HIERARCH REQ SUNALT MAX": -12.0,
        "HIERARCH REQ SUNALT DIR": "setting",
    }


def test_time_window_as_utc_iso_strings() -> None:
    start = Time("2026-10-13T20:15:00")
    constraint = TimeConstraint(start=start, end=start + 1.5 * u.hour)
    assert values(constraint.get_fits_headers(1)) == {
        "HIERARCH REQ TIME START": "2026-10-13T20:15:00.000",
        "HIERARCH REQ TIME END": "2026-10-13T21:45:00.000",
    }


def test_later_constraint_of_a_type_gets_a_number_on_the_type_token() -> None:
    assert set(SolarElevationConstraint().get_fits_headers(2)) == {
        "HIERARCH REQ SUNALT2 MAX",
        "HIERARCH REQ SUNALT2 DIR",
    }
    assert set(AirmassConstraint().get_fits_headers(3)) == {"HIERARCH REQ AIRMASS3 MAX"}
    assert set(TimeConstraint().get_fits_headers(2)) == {"HIERARCH REQ TIME2 START", "HIERARCH REQ TIME2 END"}


def test_constraint_without_override_writes_nothing() -> None:
    class PluginConstraint(Constraint):
        def to_astroplan(self):  # type: ignore[no-untyped-def]
            raise NotImplementedError

        async def __call__(self, time, task, data) -> bool:  # type: ignore[no-untyped-def]
            return True

    assert PluginConstraint().get_fits_headers(1) == {}


def test_plugin_constraint_declares_token_and_fields() -> None:
    class PluginConstraint(Constraint):
        req_token: ClassVar[str | None] = "SEEING"

        def req_fields(self) -> dict[str, tuple[int | float | str, str]]:
            return {"MAX": (2.5, "arcsec")}

        def to_astroplan(self):  # type: ignore[no-untyped-def]
            raise NotImplementedError

        async def __call__(self, time, task, data) -> bool:  # type: ignore[no-untyped-def]
            return True

    assert values(PluginConstraint().get_fits_headers(1)) == {"HIERARCH REQ SEEING MAX": 2.5}
    assert set(PluginConstraint().get_fits_headers(2)) == {"HIERARCH REQ SEEING2 MAX"}


@pytest.mark.parametrize("index", [1, 9])
def test_every_card_fits_into_80_characters(index: int) -> None:
    far = Time("2026-10-13T20:15:00.123")
    constraints: list[Constraint] = [
        AirmassConstraint(max_airmass=9.9),
        MoonSeparationConstraint(min_distance=180.0),
        MoonIlluminationConstraint(max_phase=0.123456789),
        SolarElevationConstraint(min_elevation=-89.999999, max_elevation=-17.999999, direction="setting"),
        TimeConstraint(start=far, end=far + 1.0 * u.day),
    ]
    headers = {}
    for constraint in constraints:
        headers.update(constraint.get_fits_headers(index))
    headers["HIERARCH REQ PRIORITY"] = FitsHeaderEntry(9999.0, "")
    headers["HIERARCH REQ PROJECT PRIORITY"] = FitsHeaderEntry(9999.0, "")

    for key, entry in headers.items():
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # truncation of a comment or a CONTINUE card warns
            card = fits.Card(key, entry.value, entry.comment)
            image = str(card)
        assert len(image) == 80, key
        assert card.comment == entry.comment, key
