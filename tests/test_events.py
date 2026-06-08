from __future__ import annotations

import json

import pytest

from pyobs.events import (
    BadWeatherEvent,
    ExposureStatusChangedEvent,
    FilterChangedEvent,
    FocusFoundEvent,
    GoodWeatherEvent,
    LogEvent,
    ModeChangedEvent,
    ModuleClosedEvent,
    ModuleOpenedEvent,
    MotionStatusChangedEvent,
    MoveAltAzEvent,
    MoveRaDecEvent,
    NewImageEvent,
    NewSpectrumEvent,
    OffsetsAltAzEvent,
    OffsetsRaDecEvent,
    RoofClosingEvent,
    RoofOpenedEvent,
    TaskFailedEvent,
    TaskFinishedEvent,
    TaskStartedEvent,
    TestEvent,
)
from pyobs.events.event import EventFactory
from pyobs.utils.enums import ExposureStatus, ImageType, MotionStatus
from pyobs.utils.time import Time

# ── Event base class ──────────────────────────────────────────────────────────


def test_event_has_uuid() -> None:
    e = BadWeatherEvent()
    assert isinstance(e.uuid, str) and len(e.uuid) == 36


def test_event_has_timestamp() -> None:
    e = BadWeatherEvent()
    assert isinstance(e.timestamp, float) and e.timestamp > 0


def test_event_to_json() -> None:
    e = BadWeatherEvent()
    d = e.to_json()
    assert d["type"] == "BadWeatherEvent"
    assert "uuid" in d and "timestamp" in d and "data" in d


def test_event_str_is_json() -> None:
    e = BadWeatherEvent()
    parsed = json.loads(str(e))
    assert parsed["type"] == "BadWeatherEvent"


def test_event_unique_uuids() -> None:
    e1, e2 = BadWeatherEvent(), BadWeatherEvent()
    assert e1.uuid != e2.uuid


# ── EventFactory ──────────────────────────────────────────────────────────────


def test_factory_roundtrip() -> None:
    e = BadWeatherEvent()
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, BadWeatherEvent)
    assert result.uuid == e.uuid
    assert result.timestamp == e.timestamp


def test_factory_unknown_type_returns_none() -> None:
    result = EventFactory.from_dict({"type": "NonExistentEvent", "data": {}, "uuid": "x", "timestamp": 0.0})
    assert result is None


def test_factory_missing_timestamp_defaults_to_zero() -> None:
    e = BadWeatherEvent()
    d = e.to_json()
    del d["timestamp"]
    result = EventFactory.from_dict(d)
    assert result.timestamp == 0


def test_factory_invalid_data_logs_warning(caplog) -> None:
    import logging

    with caplog.at_level(logging.WARNING):
        result = EventFactory.from_dict(
            {
                "type": "ExposureStatusChangedEvent",
                "data": {"current": "invalid_status"},
                "uuid": "x",
                "timestamp": 0.0,
            }
        )
    assert result is None
    assert "Could not create event" in caplog.text


def test_factory_none_data_treated_as_empty() -> None:
    e = BadWeatherEvent()
    d = e.to_json()
    d["data"] = None
    result = EventFactory.from_dict(d)
    assert isinstance(result, BadWeatherEvent)


# ── Marker events (no data) ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "cls,local",
    [
        (BadWeatherEvent, False),
        (RoofClosingEvent, False),
        (RoofOpenedEvent, False),
        (ModuleClosedEvent, True),
        (ModuleOpenedEvent, True),
    ],
)
def test_marker_event(cls, local) -> None:
    e = cls()
    assert e.data == {}
    assert cls.local is local
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, cls)


# ── ExposureStatusChangedEvent ────────────────────────────────────────────────


def test_exposure_status_changed_properties() -> None:
    e = ExposureStatusChangedEvent(current=ExposureStatus.EXPOSING, last=ExposureStatus.IDLE)
    assert e.current == ExposureStatus.EXPOSING
    assert e.last == ExposureStatus.IDLE


def test_exposure_status_changed_no_last() -> None:
    e = ExposureStatusChangedEvent(current=ExposureStatus.EXPOSING)
    assert e.last is None


def test_exposure_status_changed_roundtrip() -> None:
    e = ExposureStatusChangedEvent(current=ExposureStatus.EXPOSING, last=ExposureStatus.IDLE)
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, ExposureStatusChangedEvent)
    assert result.current == ExposureStatus.EXPOSING
    assert result.last == ExposureStatus.IDLE


def test_exposure_status_invalid_current() -> None:
    with pytest.raises(ValueError):
        ExposureStatusChangedEvent.from_dict({"current": 123})


# ── FilterChangedEvent ────────────────────────────────────────────────────────


def test_filter_changed_properties() -> None:
    e = FilterChangedEvent(current="V")
    assert e.filter == "V"


def test_filter_changed_roundtrip() -> None:
    e = FilterChangedEvent(current="R")
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, FilterChangedEvent)
    assert result.filter == "R"


# ── FocusFoundEvent ───────────────────────────────────────────────────────────


def test_focus_found_properties() -> None:
    e = FocusFoundEvent(focus=1.23, error=0.05, filter_name="V")
    assert e.focus == 1.23
    assert e.error == 0.05
    assert e.filter_name == "V"


def test_focus_found_optional_fields_none() -> None:
    e = FocusFoundEvent(focus=1.23)
    assert e.error is None
    assert e.filter_name is None


def test_focus_found_roundtrip() -> None:
    e = FocusFoundEvent(focus=2.5, error=0.1, filter_name="R")
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, FocusFoundEvent)
    assert result.focus == 2.5
    assert result.error == 0.1
    assert result.filter_name == "R"


# ── GoodWeatherEvent ──────────────────────────────────────────────────────────


def test_good_weather_with_eta() -> None:
    eta = Time("2025-11-03T23:00:00", scale="utc")
    e = GoodWeatherEvent(eta=eta)
    assert e.eta is not None
    assert e.eta.isot == eta.isot


def test_good_weather_no_eta() -> None:
    e = GoodWeatherEvent()
    assert e.eta is None


def test_good_weather_roundtrip() -> None:
    eta = Time("2025-11-03T23:00:00", scale="utc")
    e = GoodWeatherEvent(eta=eta)
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, GoodWeatherEvent)
    assert result.eta.isot == eta.isot


# ── LogEvent ──────────────────────────────────────────────────────────────────


def test_log_event_properties() -> None:
    e = LogEvent(time="2025-01-01", level="INFO", filename="test.py", function="test_func", line=42, message="hello")
    assert e.level == "INFO"
    assert e.filename == "test.py"
    assert e.function == "test_func"
    assert e.line == 42
    assert e.message == "hello"


def test_log_event_roundtrip() -> None:
    e = LogEvent(time="2025-01-01", level="ERROR", filename="app.py", function="run", line=10, message="oops")
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, LogEvent)
    assert result.message == "oops"
    assert result.level == "ERROR"


# ── ModeChangedEvent ──────────────────────────────────────────────────────────


def test_mode_changed_properties() -> None:
    e = ModeChangedEvent(group="filter", current="imaging")
    assert e.mode == "imaging"
    assert e.group == "filter"


def test_mode_changed_roundtrip() -> None:
    e = ModeChangedEvent(group="fiber", current="spectroscopy")
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, ModeChangedEvent)
    assert result.mode == "spectroscopy"
    assert result.group == "fiber"


# ── MotionStatusChangedEvent ──────────────────────────────────────────────────


def test_motion_status_properties() -> None:
    e = MotionStatusChangedEvent(status=MotionStatus.TRACKING, interfaces={"ITelescope": MotionStatus.TRACKING})
    assert e.status == MotionStatus.TRACKING
    assert e.interfaces["ITelescope"] == MotionStatus.TRACKING


def test_motion_status_no_interfaces() -> None:
    e = MotionStatusChangedEvent(status=MotionStatus.IDLE)
    assert e.interfaces == {}


def test_motion_status_roundtrip() -> None:
    e = MotionStatusChangedEvent(status=MotionStatus.SLEWING, interfaces={"ITelescope": MotionStatus.SLEWING})
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, MotionStatusChangedEvent)
    assert result.status == MotionStatus.SLEWING
    assert result.interfaces["ITelescope"] == MotionStatus.SLEWING


def test_motion_status_invalid_status() -> None:
    with pytest.raises(ValueError):
        MotionStatusChangedEvent.from_dict({"status": 123})


# ── MoveRaDecEvent / MoveAltAzEvent ───────────────────────────────────────────


def test_move_radec_properties() -> None:
    e = MoveRaDecEvent(ra=83.82, dec=7.41)
    assert e.ra == 83.82
    assert e.dec == 7.41


def test_move_radec_roundtrip() -> None:
    e = MoveRaDecEvent(ra=83.82, dec=7.41)
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, MoveRaDecEvent)
    assert result.ra == 83.82


def test_move_altaz_properties() -> None:
    e = MoveAltAzEvent(alt=45.0, az=180.0)
    assert e.alt == 45.0
    assert e.az == 180.0


def test_move_altaz_roundtrip() -> None:
    e = MoveAltAzEvent(alt=30.0, az=90.0)
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, MoveAltAzEvent)
    assert result.az == 90.0


# ── NewImageEvent ─────────────────────────────────────────────────────────────


def test_new_image_properties() -> None:
    e = NewImageEvent(filename="img.fits", image_type=ImageType.OBJECT, raw="raw.fits")
    assert e.filename == "img.fits"
    assert e.image_type == ImageType.OBJECT
    assert e.raw == "raw.fits"
    assert e.is_reduced is True


def test_new_image_not_reduced() -> None:
    e = NewImageEvent(filename="raw.fits", image_type=ImageType.OBJECT)
    assert e.is_reduced is False
    assert e.raw is None


def test_new_image_no_image_type() -> None:
    e = NewImageEvent(filename="img.fits")
    assert e.image_type is None


def test_new_image_roundtrip() -> None:
    e = NewImageEvent(filename="img.fits", image_type=ImageType.BIAS)
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, NewImageEvent)
    assert result.filename == "img.fits"
    assert result.image_type == ImageType.BIAS


def test_new_image_invalid_filename() -> None:
    with pytest.raises(ValueError):
        NewImageEvent.from_dict({"filename": 123})


# ── NewSpectrumEvent ──────────────────────────────────────────────────────────


def test_new_spectrum_properties() -> None:
    e = NewSpectrumEvent(filename="spec.fits")
    assert e.filename == "spec.fits"


def test_new_spectrum_roundtrip() -> None:
    e = NewSpectrumEvent(filename="spec.fits")
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, NewSpectrumEvent)
    assert result.filename == "spec.fits"


def test_new_spectrum_invalid_filename() -> None:
    with pytest.raises(ValueError):
        NewSpectrumEvent.from_dict({"filename": 42})


# ── OffsetsRaDecEvent / OffsetsAltAzEvent ────────────────────────────────────


def test_offsets_radec_properties() -> None:
    e = OffsetsRaDecEvent(ra=1.5, dec=-0.5)
    assert e.ra == 1.5
    assert e.dec == -0.5


def test_offsets_radec_roundtrip() -> None:
    e = OffsetsRaDecEvent(ra=0.1, dec=0.2)
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, OffsetsRaDecEvent)
    assert result.ra == 0.1


def test_offsets_altaz_properties() -> None:
    e = OffsetsAltAzEvent(alt=0.5, az=1.0)
    assert e.alt == 0.5
    assert e.az == 1.0


def test_offsets_altaz_roundtrip() -> None:
    e = OffsetsAltAzEvent(alt=0.3, az=0.4)
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, OffsetsAltAzEvent)
    assert result.az == 0.4


# ── TaskStartedEvent ──────────────────────────────────────────────────────────


def test_task_started_properties() -> None:
    eta = Time("2025-11-03T23:30:00", scale="utc")
    e = TaskStartedEvent(name="Kochab", id=42, eta=eta)
    assert e.name == "Kochab"
    assert e.id == 42
    assert e.eta.isot == eta.isot


def test_task_started_no_eta() -> None:
    e = TaskStartedEvent(name="Vega", id=1)
    assert e.eta is None


def test_task_started_roundtrip() -> None:
    eta = Time("2025-11-03T23:00:00", scale="utc")
    e = TaskStartedEvent(name="Kochab", id=99, eta=eta)
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, TaskStartedEvent)
    assert result.name == "Kochab"
    assert result.id == 99
    assert result.eta.isot == eta.isot


def test_task_started_invalid_name() -> None:
    with pytest.raises(ValueError):
        TaskStartedEvent.from_dict({"name": 123, "id": 1})


def test_task_started_missing_id() -> None:
    with pytest.raises(ValueError):
        TaskStartedEvent.from_dict({"name": "Kochab"})


# ── TaskFinishedEvent / TaskFailedEvent ───────────────────────────────────────


def test_task_finished_properties() -> None:
    e = TaskFinishedEvent(name="Kochab", id=42)
    assert e.name == "Kochab"
    assert e.id == 42


def test_task_finished_roundtrip() -> None:
    e = TaskFinishedEvent(name="Vega", id=7)
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, TaskFinishedEvent)
    assert result.name == "Vega"
    assert result.id == 7


def test_task_failed_properties() -> None:
    e = TaskFailedEvent(name="Kochab", id=42)
    assert e.name == "Kochab"
    assert e.id == 42


def test_task_failed_roundtrip() -> None:
    e = TaskFailedEvent(name="Sirius", id=3)
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, TaskFailedEvent)
    assert result.name == "Sirius"


# ── TestEvent ─────────────────────────────────────────────────────────────────


def test_test_event_with_message() -> None:
    e = TestEvent(message="hello")
    assert e.data["message"] == "hello"


def test_test_event_no_message() -> None:
    e = TestEvent()
    assert e.data["message"] is None


def test_test_event_roundtrip() -> None:
    e = TestEvent(message="ping")
    result = EventFactory.from_dict(e.to_json())
    assert isinstance(result, TestEvent)
