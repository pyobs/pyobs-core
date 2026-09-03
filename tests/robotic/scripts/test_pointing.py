from __future__ import annotations

from unittest.mock import MagicMock

from pyobs.robotic.instruments import Instrument, InstrumentCapabilities, TelescopeCapability
from pyobs.robotic.scripts.calibration.pointing import PointingScript
from pyobs.robotic.task import TaskData
from pyobs.robotic.utils.skyflats.pointing.static import SkyFlatsStaticPointing


def make_script(**kwargs) -> PointingScript:
    return PointingScript.model_validate(
        {"telescope": "telescope", "pointing": SkyFlatsStaticPointing(), **kwargs}, context={"comm": MagicMock()}
    )


def test_estimate_duration_falls_back_without_capabilities() -> None:
    script = make_script()
    assert script.estimate_duration(None) == 60.0


def test_estimate_duration_uses_real_slew_rate_when_available() -> None:
    script = make_script()
    telescope_capability = TelescopeCapability(module_name="telescope", slew_rate_deg_per_s=3.0)
    capabilities = InstrumentCapabilities([Instrument(telescope=telescope_capability)])
    data = TaskData(task=MagicMock(), instrument_capabilities=capabilities)

    duration = script.estimate_duration(data)

    assert duration == telescope_capability.estimate_slew_time_s()
    assert duration != 60.0  # sanity: the real rate actually changed the estimate


def test_estimate_duration_falls_back_when_telescope_module_not_matched() -> None:
    script = make_script()
    capabilities = InstrumentCapabilities(
        [Instrument(telescope=TelescopeCapability(module_name="a-different-telescope", slew_rate_deg_per_s=3.0))]
    )
    data = TaskData(task=MagicMock(), instrument_capabilities=capabilities)

    assert script.estimate_duration(data) == 60.0
