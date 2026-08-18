from __future__ import annotations

from pyobs.object import Object
from pyobs.robotic.scheduler.constraints import Constraint
from pyobs.robotic.scheduler.constraints.airmassconstraint import AirmassConstraint


def test_create_with_type_shorthand_does_not_raise() -> None:
    """Regression test: Constraint.create() derives `class` from the `type` shorthand but must not
    leave `type` itself in the config dict, or extra="forbid" rejects it as an unrecognized field."""
    constraint = Constraint.create(Object(), {"type": "Airmass", "max_airmass": 1.5})

    assert isinstance(constraint, AirmassConstraint)
    assert constraint.max_airmass == 1.5
