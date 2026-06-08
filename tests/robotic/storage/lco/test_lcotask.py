from __future__ import annotations

import json

import pytest

from pyobs.robotic.scheduler.constraints import (
    AirmassConstraint,
    MoonIlluminationConstraint,
    MoonSeparationConstraint,
    SolarElevationConstraint,
    TimeConstraint,
)
from pyobs.robotic.scheduler.merits import PerNightMerit
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.robotic.storage.lco import LcoTask
from pyobs.robotic.storage.lco._portal import LcoSchedulableRequest

from .test_task import REQUEST_CONFIG

# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def schedulable_request() -> LcoSchedulableRequest:
    return LcoSchedulableRequest.model_validate(json.loads(REQUEST_CONFIG))


@pytest.fixture
def task(schedulable_request: LcoSchedulableRequest) -> LcoTask:
    tasks = LcoTask.from_schedulable_request(schedulable_request, {})
    return tasks[0]


# ── constraints ───────────────────────────────────────────────────────────────


def test_constraints_created_from_request(task: LcoTask) -> None:
    """Correct number and types of constraints created from a request."""
    types = [type(c) for c in task.constraints]
    assert AirmassConstraint in types
    assert MoonSeparationConstraint in types
    assert MoonIlluminationConstraint in types
    assert TimeConstraint in types


def test_adds_solar_elevation_constraint_for_dark_sky() -> None:
    """max_lunar_phase <= 0.4 adds a SolarElevationConstraint."""
    config = json.loads(REQUEST_CONFIG)
    config["requests"][0]["configurations"][0]["constraints"]["max_lunar_phase"] = 0.3
    sr = LcoSchedulableRequest.model_validate(config)
    task = LcoTask.from_schedulable_request(sr, {})[0]

    solar = [c for c in task.constraints if isinstance(c, SolarElevationConstraint)]
    assert len(solar) == 1
    assert solar[0].max_elevation == -18.0


def test_no_solar_elevation_constraint_for_bright_sky() -> None:
    """max_lunar_phase > 0.4 does not add a SolarElevationConstraint."""
    config = json.loads(REQUEST_CONFIG)
    config["requests"][0]["configurations"][0]["constraints"]["max_lunar_phase"] = 0.7
    sr = LcoSchedulableRequest.model_validate(config)
    task = LcoTask.from_schedulable_request(sr, {})[0]

    solar = [c for c in task.constraints if isinstance(c, SolarElevationConstraint)]
    assert len(solar) == 0


# ── merits ────────────────────────────────────────────────────────────────────


def test_creates_merits_from_config(task: LcoTask) -> None:
    assert len(task.merits) == 1
    assert isinstance(task.merits[0], PerNightMerit)
    assert task.merits[0].count == 3


# ── target ────────────────────────────────────────────────────────────────────


def test_creates_sidereal_target(task: LcoTask) -> None:
    assert isinstance(task.target, SiderealTarget)
    assert task.target.name == "Kochab"
    assert abs(task.target.ra - 222.676) < 0.01
    assert abs(task.target.dec - 74.155) < 0.01


# ── task properties ───────────────────────────────────────────────────────────


def test_can_start_late_false_for_normal(task: LcoTask) -> None:
    assert task.can_start_late is False


def test_can_start_late_true_for_direct() -> None:
    config = json.loads(REQUEST_CONFIG)
    config["requests"][0]["configurations"][0]["type"] = "DIRECT"
    sr = LcoSchedulableRequest.model_validate(config)
    task = LcoTask.from_schedulable_request(sr, {})[0]
    assert task.can_start_late is True


def test_is_finished_false_when_pending(task: LcoTask) -> None:
    assert task.is_finished() is False


def test_is_finished_true_when_not_pending(task: LcoTask) -> None:
    task.request.configurations[0].state = "COMPLETED"
    assert task.is_finished() is True


def test_task_id_and_duration(task: LcoTask) -> None:
    assert task.id == 94320
    assert task.duration == 1925


# ── from_observation ──────────────────────────────────────────────────────────


def test_from_observation(schedulable_request: LcoSchedulableRequest) -> None:
    """LcoTask.from_observation creates a task from an LcoObservation."""
    from pyobs.robotic.storage.lco._portal import LcoObservation

    obs_json = {
        "id": 1,
        "request": json.loads(REQUEST_CONFIG)["requests"][0],
        "site": "saao",
        "enclosure": "aqwa",
        "telescope": "0m4a",
        "start": "2026-01-01T00:00:00Z",
        "end": "2026-01-01T00:30:00Z",
        "priority": 10,
        "state": "PENDING",
    }
    obs = LcoObservation.model_validate(obs_json)
    task = LcoTask.from_observation(obs, {})

    assert task.name == str(obs.request.id)
    assert isinstance(task.target, SiderealTarget)
    assert task.target.name == "Kochab"
