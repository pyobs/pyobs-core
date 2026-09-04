from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from pyobs.robotic.instruments import (
    DomeCapability,
    Instrument,
    InstrumentCapabilities,
    RoofCapability,
    TelescopeCapability,
)

# One Instrument's InstrumentSerializer output, dumped from a live pyobs-portal instance
# (pyobs-portal#142's schema: module_name lives on CameraCapability/TelescopeCapability/
# DomeCapability/FilterWheelCapability, not on Instrument itself) -- confirmed against the actual
# serializer output, not just hand-guessed field names.
INSTRUMENT_RESPONSE: dict[str, Any] = {
    "display_name": "GOE 50cm",
    "notes": "Main telescope",
    "updated_at": "2026-09-02T18:34:16.451210Z",
    "cameras": [
        {
            "module_name": "iag50cam",
            "code": "ef01",
            "model": "FLI ProLine PL23042",
            "sensor_type": "e2v CCD230-42, back-illuminated CCD",
            "pixel_size_um": 5.4,
            "sensor_width_px": 4096,
            "sensor_height_px": 4096,
            "roi_min_width_px": None,
            "roi_min_height_px": None,
            "roi_step_px": None,
            "exposure_time_min_s": 0.001,
            "exposure_time_max_s": 3600.0,
            "image_types": ["object", "bias", "dark", "flat"],
            "updated_at": "2026-09-02T18:34:16.452157Z",
            "binnings": [
                {"x": 1, "y": 1, "readout_time_s": 3.2, "updated_at": "2026-09-02T18:34:16.452608Z"},
                {"x": 2, "y": 2, "readout_time_s": 1.8, "updated_at": "2026-09-02T18:34:16.452879Z"},
            ],
            "filter_wheels": [
                {
                    "name": "",
                    "module_name": "iag50filt",
                    "model": "FLI CFW-2-7",
                    "filter_change_time_s": 4.5,
                    "updated_at": "2026-09-02T18:34:16.453140Z",
                    "filters": [
                        {"name": "R", "position": 1, "updated_at": "2026-09-02T18:34:16.453420Z"},
                        {"name": "V", "position": 2, "updated_at": "2026-09-02T18:34:16.453663Z"},
                    ],
                }
            ],
        }
    ],
    "telescope": {
        "module_name": "iag50telescope",
        "aperture_mm": 500.0,
        "focal_length_mm": 4000.0,
        "mount_type": "fork",
        "slew_rate_deg_per_s": 3.0,
        "updated_at": "2026-09-02T18:34:16.453947Z",
    },
    "dome": {
        "module_name": "iag50dome",
        "rotate_rate_deg_per_s": 2.5,
        "updated_at": "2026-09-02T18:34:16.454272Z",
    },
    "roof": None,
}


def test_instrument_round_trips_portal_response() -> None:
    instrument = Instrument.model_validate(INSTRUMENT_RESPONSE)
    assert instrument.display_name == "GOE 50cm"
    camera = instrument.cameras[0]
    assert camera.module_name == "iag50cam"
    assert camera.code == "ef01"
    assert camera.model == "FLI ProLine PL23042"
    assert camera.sensor_type == "e2v CCD230-42, back-illuminated CCD"
    assert [(b.x, b.y, b.readout_time_s) for b in camera.binnings] == [(1, 1, 3.2), (2, 2, 1.8)]
    wheel = camera.filter_wheels[0]
    assert wheel.module_name == "iag50filt"
    assert wheel.model == "FLI CFW-2-7"
    assert wheel.filter_change_time_s == 4.5
    assert [f.name for f in wheel.filters] == ["R", "V"]
    assert instrument.telescope is not None
    assert instrument.telescope.module_name == "iag50telescope"
    assert instrument.telescope.slew_rate_deg_per_s == 3.0
    assert instrument.dome is not None
    assert instrument.dome.module_name == "iag50dome"
    assert instrument.dome.rotate_rate_deg_per_s == 2.5
    assert instrument.roof is None


def test_instrument_with_plain_roof_round_trips() -> None:
    # a plain-roof site has no dome at all -- MONET-N/S per monet/pyobs-monet#3
    response = {
        **INSTRUMENT_RESPONSE,
        "dome": None,
        "roof": {
            "module_name": "iag50roof",
            "open_close_time_s": 45.0,
            "updated_at": "2026-09-04T09:00:00.000000Z",
        },
    }
    instrument = Instrument.model_validate(response)
    assert instrument.dome is None
    assert instrument.roof is not None
    assert instrument.roof.module_name == "iag50roof"
    assert instrument.roof.open_close_time_s == 45.0


def test_instrument_tolerates_unknown_fields() -> None:
    # a running process can be on an older pyobs-core release than whatever portal it polls --
    # an unrecognized field (the portal gained one, or will) must degrade gracefully, not raise.
    response = {
        **INSTRUMENT_RESPONSE,
        "some_future_field": "unexpected",
        "cameras": [{**INSTRUMENT_RESPONSE["cameras"][0], "some_future_camera_field": 123}],
        "telescope": {**INSTRUMENT_RESPONSE["telescope"], "some_future_telescope_field": True},
    }
    instrument = Instrument.model_validate(response)
    assert instrument.display_name == "GOE 50cm"
    assert instrument.cameras[0].module_name == "iag50cam"
    assert instrument.telescope is not None
    assert instrument.telescope.module_name == "iag50telescope"


def test_instrument_with_no_telescope_or_dome() -> None:
    response = {**INSTRUMENT_RESPONSE, "telescope": None, "dome": None}
    instrument = Instrument.model_validate(response)
    assert instrument.telescope is None
    assert instrument.dome is None
    assert instrument.roof is None


class TestInstrumentCapabilities:
    def setup_method(self) -> None:
        self.capabilities = InstrumentCapabilities.from_api_response([INSTRUMENT_RESPONSE])

    def test_camera_lookup_by_module_name(self) -> None:
        camera = self.capabilities.camera("iag50cam")
        assert camera is not None
        assert camera.code == "ef01"
        assert self.capabilities.camera("no-such-module") is None

    def test_by_camera_code(self) -> None:
        camera = self.capabilities.by_camera_code("ef01")
        assert camera is not None
        assert camera.module_name == "iag50cam"
        assert self.capabilities.by_camera_code("zz99") is None

    def test_telescope_lookup_by_module_name(self) -> None:
        telescope = self.capabilities.telescope("iag50telescope")
        assert telescope is not None
        assert telescope.slew_rate_deg_per_s == 3.0
        assert self.capabilities.telescope("iag50cam") is None

    def test_dome_lookup_by_module_name(self) -> None:
        dome = self.capabilities.dome("iag50dome")
        assert dome is not None
        assert dome.rotate_rate_deg_per_s == 2.5

    def test_roof_lookup_by_module_name(self) -> None:
        response = {
            **INSTRUMENT_RESPONSE,
            "dome": None,
            "roof": {"module_name": "iag50roof", "open_close_time_s": 45.0, "updated_at": None},
        }
        capabilities = InstrumentCapabilities.from_api_response([response])
        roof = capabilities.roof("iag50roof")
        assert roof is not None
        assert roof.open_close_time_s == 45.0
        assert capabilities.roof("iag50dome") is None

    def test_filter_wheel_lookup_by_module_name(self) -> None:
        wheel = self.capabilities.filter_wheel("iag50filt")
        assert wheel is not None
        assert wheel.filter_change_time_s == 4.5

    def test_filter_wheel_requires_module_name(self) -> None:
        # module_name used to be nullable (pyobs-portal#142) -- dropped since a blank value made
        # the row permanently unreachable via filter_wheel() lookup, with no valid use case left.
        response = {
            **INSTRUMENT_RESPONSE,
            "cameras": [
                {
                    **INSTRUMENT_RESPONSE["cameras"][0],
                    "filter_wheels": [
                        {
                            "name": "unnamed",
                            "module_name": None,
                            "filter_change_time_s": 1.0,
                            "updated_at": None,
                            "filters": [],
                        }
                    ],
                }
            ],
        }
        with pytest.raises(ValidationError):
            InstrumentCapabilities.from_api_response([response])

    def test_multiple_instruments_aggregate_into_one_lookup(self) -> None:
        other = {
            **INSTRUMENT_RESPONSE,
            "display_name": "Guide scope",
            "cameras": [{**INSTRUMENT_RESPONSE["cameras"][0], "module_name": "guidecam", "code": "ef02"}],
            "telescope": {**INSTRUMENT_RESPONSE["telescope"], "module_name": "guidetelescope"},
            "dome": None,
        }
        capabilities = InstrumentCapabilities.from_api_response([INSTRUMENT_RESPONSE, other])
        assert capabilities.camera("iag50cam") is not None
        assert capabilities.camera("guidecam") is not None
        assert capabilities.telescope("guidetelescope") is not None
        assert len(capabilities.instruments) == 2


class TestTelescopeCapabilityEstimateSlewTime:
    def test_returns_typical_distance_over_rate(self) -> None:
        telescope = TelescopeCapability(module_name="tel1", slew_rate_deg_per_s=3.0)
        # 90.0 deg (the documented placeholder distance) / 3.0 deg/s
        assert telescope.estimate_slew_time_s() == pytest.approx(30.0)

    def test_none_when_rate_not_declared(self) -> None:
        telescope = TelescopeCapability(module_name="tel1")
        assert telescope.estimate_slew_time_s() is None

    def test_none_when_rate_is_zero_or_negative(self) -> None:
        assert TelescopeCapability(module_name="tel1", slew_rate_deg_per_s=0.0).estimate_slew_time_s() is None
        assert TelescopeCapability(module_name="tel1", slew_rate_deg_per_s=-1.0).estimate_slew_time_s() is None

    def test_distance_deg_overrides_the_default(self) -> None:
        telescope = TelescopeCapability(module_name="tel1", slew_rate_deg_per_s=3.0)
        assert telescope.estimate_slew_time_s(distance_deg=15.0) == pytest.approx(5.0)


class TestDomeCapabilityEstimateRotateTime:
    def test_returns_typical_distance_over_rate(self) -> None:
        dome = DomeCapability(module_name="dome1", rotate_rate_deg_per_s=2.5)
        # 90.0 deg (the same shared placeholder distance as the telescope) / 2.5 deg/s
        assert dome.estimate_rotate_time_s() == pytest.approx(36.0)

    def test_none_when_rate_not_declared(self) -> None:
        dome = DomeCapability(module_name="dome1")
        assert dome.estimate_rotate_time_s() is None

    def test_none_when_rate_is_zero_or_negative(self) -> None:
        assert DomeCapability(module_name="dome1", rotate_rate_deg_per_s=0.0).estimate_rotate_time_s() is None
        assert DomeCapability(module_name="dome1", rotate_rate_deg_per_s=-1.0).estimate_rotate_time_s() is None

    def test_distance_deg_overrides_the_default(self) -> None:
        dome = DomeCapability(module_name="dome1", rotate_rate_deg_per_s=2.5)
        assert dome.estimate_rotate_time_s(distance_deg=10.0) == pytest.approx(4.0)


class TestRoofCapability:
    def test_open_close_time_s_defaults_to_none(self) -> None:
        assert RoofCapability(module_name="roof1").open_close_time_s is None

    def test_open_close_time_s_used_directly_not_a_rate(self) -> None:
        # unlike TelescopeCapability/DomeCapability, this is already a duration -- no
        # estimate_*() method, no distance parameter to combine it with.
        roof = RoofCapability(module_name="roof1", open_close_time_s=45.0)
        assert roof.open_close_time_s == 45.0
