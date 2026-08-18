from __future__ import annotations

from pyobs.robotic.scheduler.merits import Merit
from pyobs.robotic.scheduler.merits.pernight import PerNightMerit


def test_create_with_type_shorthand_does_not_raise() -> None:
    """Regression test: Merit.create() derives `class` from the `type` shorthand but must not
    leave `type` itself in the config dict, or extra="forbid" rejects it as an unrecognized field."""
    merit = Merit.create({"type": "PerNight", "count": 3})

    assert isinstance(merit, PerNightMerit)
    assert merit.count == 3
