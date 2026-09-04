from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from pyobs.robotic.instruments import (
    BinningOption,
    CameraCapability,
    DomeCapability,
    FilterWheelCapability,
    Instrument,
    InstrumentCapabilities,
    TelescopeCapability,
)
from pyobs.robotic.scripts.imaging.imaging import Configuration, ImagingScript, InstrumentConfig
from pyobs.robotic.task import TaskData


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


# ── estimate_duration ────────────────────────────────────────────────────────


def make_script(**kwargs) -> ImagingScript:
    return ImagingScript.model_validate({"camera": "camera", **kwargs}, context={"comm": MagicMock()})


def test_estimate_duration_falls_back_without_capabilities() -> None:
    script = make_script(
        configuration={
            "instrument_configs": [{"exposure_time": 30.0, "count": 2}],
            "repeats": 1,
            "acquisition_config": {"enabled": False},
        }
    )
    # no readout, no filter-change, flat 60.0 slew fudge -- exactly today's formula
    assert script.estimate_duration(None) == 30.0 * 2 + 60.0


def test_estimate_duration_adds_real_readout_time() -> None:
    script = make_script(
        camera="cam1",
        configuration={
            "instrument_configs": [{"exposure_time": 30.0, "count": 2, "binning": (2, 2)}],
            "repeats": 1,
            "acquisition_config": {"enabled": False},
        },
    )
    camera_capability = CameraCapability(
        module_name="cam1", code="ef01", binnings=[BinningOption(x=2, y=2, readout_time_s=3.5)]
    )
    data = TaskData(
        task=MagicMock(), instrument_capabilities=InstrumentCapabilities([Instrument(cameras=[camera_capability])])
    )

    duration = script.estimate_duration(data)

    assert duration == (30.0 + 3.5) * 2 + 60.0


def test_estimate_duration_no_readout_added_when_binning_not_declared() -> None:
    script = make_script(
        camera="cam1",
        configuration={
            "instrument_configs": [{"exposure_time": 30.0, "count": 2, "binning": (2, 2)}],
            "repeats": 1,
            "acquisition_config": {"enabled": False},
        },
    )
    camera_capability = CameraCapability(
        module_name="cam1", code="ef01", binnings=[BinningOption(x=1, y=1, readout_time_s=3.5)]
    )
    data = TaskData(
        task=MagicMock(), instrument_capabilities=InstrumentCapabilities([Instrument(cameras=[camera_capability])])
    )

    assert script.estimate_duration(data) == 30.0 * 2 + 60.0


def test_estimate_duration_uses_real_slew_rate() -> None:
    script = make_script(
        telescope="tel1",
        configuration={
            "instrument_configs": [{"exposure_time": 30.0, "count": 1}],
            "repeats": 1,
            "acquisition_config": {"enabled": False},
        },
    )
    telescope_capability = TelescopeCapability(module_name="tel1", slew_rate_deg_per_s=3.0)
    data = TaskData(
        task=MagicMock(), instrument_capabilities=InstrumentCapabilities([Instrument(telescope=telescope_capability)])
    )

    duration = script.estimate_duration(data)
    slew_time = telescope_capability.estimate_slew_time_s()
    assert slew_time is not None

    assert duration == 30.0 + slew_time
    assert duration != 30.0 + 60.0


def test_estimate_duration_uses_dome_rotate_time_when_slower() -> None:
    script = make_script(
        telescope="tel1",
        dome="dome1",
        configuration={
            "instrument_configs": [{"exposure_time": 30.0, "count": 1}],
            "repeats": 1,
            "acquisition_config": {"enabled": False},
        },
    )
    telescope_capability = TelescopeCapability(module_name="tel1", slew_rate_deg_per_s=3.0)  # 30.0s
    dome_capability = DomeCapability(module_name="dome1", rotate_rate_deg_per_s=1.0)  # 90.0s, slower
    data = TaskData(
        task=MagicMock(),
        instrument_capabilities=InstrumentCapabilities(
            [Instrument(telescope=telescope_capability, dome=dome_capability)]
        ),
    )

    duration = script.estimate_duration(data)
    rotate_time = dome_capability.estimate_rotate_time_s()
    assert rotate_time is not None

    assert duration == 30.0 + rotate_time
    assert duration != 30.0 + telescope_capability.estimate_slew_time_s()


def test_estimate_duration_acquisition_fudge_still_applies() -> None:
    script = make_script(
        configuration={
            "instrument_configs": [{"exposure_time": 30.0, "count": 1}],
            "repeats": 1,
            "acquisition_config": {"enabled": True},
        }
    )
    assert script.estimate_duration(None) == 30.0 + 60.0 + 30.0


def test_estimate_duration_adds_filter_change_time_for_actual_transitions() -> None:
    # R, V, V, R across one repeat -> 2 actual transitions (R->V, V->R); the middle V->V pair
    # isn't a change
    script = make_script(
        filters="wheel1",
        configuration={
            "instrument_configs": [
                {"exposure_time": 10.0, "count": 1, "optical_filter": "R"},
                {"exposure_time": 10.0, "count": 1, "optical_filter": "V"},
                {"exposure_time": 10.0, "count": 1, "optical_filter": "V"},
                {"exposure_time": 10.0, "count": 1, "optical_filter": "R"},
            ],
            "repeats": 1,
            "acquisition_config": {"enabled": False},
        },
    )
    filter_wheel = FilterWheelCapability(module_name="wheel1", filter_change_time_s=4.0)
    camera_capability = CameraCapability(module_name="camera", code="ef01", filter_wheels=[filter_wheel])
    data = TaskData(
        task=MagicMock(), instrument_capabilities=InstrumentCapabilities([Instrument(cameras=[camera_capability])])
    )

    duration = script.estimate_duration(data)

    assert duration == 40.0 + 60.0 + 2 * 4.0


def test_estimate_duration_no_filter_change_time_when_filters_unset() -> None:
    script = make_script(
        configuration={
            "instrument_configs": [
                {"exposure_time": 10.0, "count": 1, "optical_filter": "R"},
                {"exposure_time": 10.0, "count": 1, "optical_filter": "V"},
            ],
            "repeats": 1,
            "acquisition_config": {"enabled": False},
        }
    )
    # capability data exists, but self.filters is unset -- no filter wheel to look up
    filter_wheel = FilterWheelCapability(module_name="wheel1", filter_change_time_s=4.0)
    camera_capability = CameraCapability(module_name="camera", code="ef01", filter_wheels=[filter_wheel])
    data = TaskData(
        task=MagicMock(), instrument_capabilities=InstrumentCapabilities([Instrument(cameras=[camera_capability])])
    )

    assert script.estimate_duration(data) == 20.0 + 60.0


def test_filter_change_count_ignores_transitions_touching_unset_filter() -> None:
    script = make_script(
        configuration={
            "instrument_configs": [
                InstrumentConfig(exposure_time=1.0, optical_filter="R"),
                InstrumentConfig(exposure_time=1.0, optical_filter=None),
                InstrumentConfig(exposure_time=1.0, optical_filter="V"),
            ],
            "repeats": 1,
        }
    )
    assert script._filter_change_count() == 0


def test_filter_change_count_wraps_across_repeats() -> None:
    script = make_script(
        configuration={
            "instrument_configs": [
                InstrumentConfig(exposure_time=1.0, optical_filter="R"),
                InstrumentConfig(exposure_time=1.0, optical_filter="V"),
            ],
            "repeats": 2,
        }
    )
    # R, V | R, V -- transitions: R->V, V->R, R->V = 3
    assert script._filter_change_count() == 3
