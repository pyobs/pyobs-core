from __future__ import annotations

import math

import pytest

from pyobs.robotic.scheduler import constraints as constraints_module
from pyobs.robotic.scheduler import merits as merits_module
from pyobs.robotic.scheduler.constraints import (
    AirmassConstraint,
    Constraint,
    MoonSeparationConstraint,
    SolarElevationConstraint,
    TimeConstraint,
    TimeOfDayConstraint,
)
from pyobs.robotic.scheduler.constraints.constraint import STRICTER_KEY
from pyobs.robotic.scheduler.merits import ConstantMerit, Merit, PerNightMerit, RandomMerit
from pyobs.robotic.scheduler.merits.merit import MERIT_FACTOR_KEY


def test_stricter_fields() -> None:
    assert AirmassConstraint.stricter_fields() == {"max_airmass": "lower"}
    assert MoonSeparationConstraint.stricter_fields() == {"min_distance": "higher"}
    assert SolarElevationConstraint.stricter_fields() == {"min_elevation": "higher", "max_elevation": "lower"}
    assert TimeConstraint.stricter_fields() == {"start": "higher", "end": "lower"}
    assert TimeOfDayConstraint.stricter_fields() == {}


def test_stricter_in_json_schema() -> None:
    props = AirmassConstraint.model_json_schema()["properties"]
    assert props["max_airmass"][STRICTER_KEY] == "lower"


def test_merit_max_values() -> None:
    assert ConstantMerit(merit=0.5).max_value() == 0.5
    assert ConstantMerit(merit=5).max_value() == 5
    assert RandomMerit(std=0.1).max_value() == math.inf
    assert RandomMerit(std=0).max_value() == 1.0
    assert PerNightMerit(count=1).max_value() == 1.0
    assert ConstantMerit.model_json_schema()["properties"]["merit"][MERIT_FACTOR_KEY] is True


@pytest.mark.parametrize(
    "name", [n for n in merits_module.__all__ if n != "Merit" and isinstance(getattr(merits_module, n), type)]
)
def test_every_core_merit_declares_max_value(name: str) -> None:
    cls = getattr(merits_module, name)
    assert issubclass(cls, Merit)
    assert cls.max_value is not Merit.max_value


def test_constraint_base_has_no_stricter_fields() -> None:
    assert all(f not in Constraint.stricter_fields() for f in ("cost", "target_dependent"))
    assert constraints_module  # imported for completeness
