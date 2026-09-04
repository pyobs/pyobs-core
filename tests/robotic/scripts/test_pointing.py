from __future__ import annotations

from unittest.mock import MagicMock

from pyobs.robotic.instruments import (
    DomeCapability,
    Instrument,
    InstrumentCapabilities,
    RoofCapability,
    TelescopeCapability,
)
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


def test_estimate_duration_uses_dome_rotate_time_when_slower() -> None:
    script = make_script(dome="dome1")
    telescope_capability = TelescopeCapability(module_name="telescope", slew_rate_deg_per_s=3.0)  # 30.0s
    dome_capability = DomeCapability(module_name="dome1", rotate_rate_deg_per_s=1.0)  # 90.0s, slower
    capabilities = InstrumentCapabilities([Instrument(telescope=telescope_capability, dome=dome_capability)])
    data = TaskData(task=MagicMock(), instrument_capabilities=capabilities)

    duration = script.estimate_duration(data)

    assert duration == dome_capability.estimate_rotate_time_s()
    assert duration != telescope_capability.estimate_slew_time_s()


def test_estimate_duration_uses_telescope_slew_time_when_slower() -> None:
    script = make_script(dome="dome1")
    telescope_capability = TelescopeCapability(module_name="telescope", slew_rate_deg_per_s=1.0)  # 90.0s, slower
    dome_capability = DomeCapability(module_name="dome1", rotate_rate_deg_per_s=3.0)  # 30.0s
    capabilities = InstrumentCapabilities([Instrument(telescope=telescope_capability, dome=dome_capability)])
    data = TaskData(task=MagicMock(), instrument_capabilities=capabilities)

    duration = script.estimate_duration(data)

    assert duration == telescope_capability.estimate_slew_time_s()
    assert duration != dome_capability.estimate_rotate_time_s()


def test_estimate_duration_ignores_dome_when_not_configured() -> None:
    script = make_script()  # no dome field set
    telescope_capability = TelescopeCapability(module_name="telescope", slew_rate_deg_per_s=3.0)
    dome_capability = DomeCapability(module_name="dome1", rotate_rate_deg_per_s=100.0)  # would dominate if used
    capabilities = InstrumentCapabilities([Instrument(telescope=telescope_capability, dome=dome_capability)])
    data = TaskData(task=MagicMock(), instrument_capabilities=capabilities)

    assert script.estimate_duration(data) == telescope_capability.estimate_slew_time_s()


def test_estimate_duration_uses_roof_open_close_time_when_slower() -> None:
    script = make_script(roof="roof1")
    telescope_capability = TelescopeCapability(module_name="telescope", slew_rate_deg_per_s=3.0)  # 30.0s
    roof_capability = RoofCapability(module_name="roof1", open_close_time_s=90.0)  # slower
    capabilities = InstrumentCapabilities([Instrument(telescope=telescope_capability, roof=roof_capability)])
    data = TaskData(task=MagicMock(), instrument_capabilities=capabilities)

    duration = script.estimate_duration(data)

    assert duration == 90.0
    assert duration != telescope_capability.estimate_slew_time_s()


def test_estimate_duration_uses_telescope_slew_time_when_slower_than_roof() -> None:
    script = make_script(roof="roof1")
    telescope_capability = TelescopeCapability(module_name="telescope", slew_rate_deg_per_s=1.0)  # 90.0s, slower
    roof_capability = RoofCapability(module_name="roof1", open_close_time_s=20.0)
    capabilities = InstrumentCapabilities([Instrument(telescope=telescope_capability, roof=roof_capability)])
    data = TaskData(task=MagicMock(), instrument_capabilities=capabilities)

    duration = script.estimate_duration(data)

    assert duration == telescope_capability.estimate_slew_time_s()


def test_estimate_duration_ignores_roof_when_not_configured() -> None:
    script = make_script()  # no roof field set
    telescope_capability = TelescopeCapability(module_name="telescope", slew_rate_deg_per_s=3.0)
    roof_capability = RoofCapability(module_name="roof1", open_close_time_s=1000.0)  # would dominate if used
    capabilities = InstrumentCapabilities([Instrument(telescope=telescope_capability, roof=roof_capability)])
    data = TaskData(task=MagicMock(), instrument_capabilities=capabilities)

    assert script.estimate_duration(data) == telescope_capability.estimate_slew_time_s()
