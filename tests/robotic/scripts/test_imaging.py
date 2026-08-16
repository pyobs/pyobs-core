from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyobs.robotic.scripts.imaging.imaging import Configuration


def test_misplaced_guiding_config_inside_instrument_configs_raises() -> None:
    """Regression test for the bug that motivated extra="forbid" on the imaging config models:
    guiding_config/acquisition_config belong on Configuration, not on an individual
    InstrumentConfig. Misplacing them there must raise instead of being silently dropped (which
    previously left the Configuration-level defaults in effect with no error)."""
    with pytest.raises(ValidationError):
        Configuration.model_validate(
            {
                "instrument_configs": [
                    {
                        "exposure_time": 30.0,
                        "guiding_config": {"enabled": False},
                        "acquisition_config": {"enabled": False},
                    }
                ],
            }
        )
