from __future__ import annotations

import json

import pytest

from pyobs.object import Object
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
    tasks = LcoTask.from_schedulable_request(Object(), schedulable_request, {})
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
    task = LcoTask.from_schedulable_request(Object(), sr, {})[0]

    solar = [c for c in task.constraints if isinstance(c, SolarElevationConstraint)]
    assert len(solar) == 1
    assert solar[0].max_elevation == -18.0


def test_no_solar_elevation_constraint_for_bright_sky() -> None:
    """max_lunar_phase > 0.4 does not add a SolarElevationConstraint."""
    config = json.loads(REQUEST_CONFIG)
    config["requests"][0]["configurations"][0]["constraints"]["max_lunar_phase"] = 0.7
    sr = LcoSchedulableRequest.model_validate(config)
    task = LcoTask.from_schedulable_request(Object(), sr, {})[0]

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
    task = LcoTask.from_schedulable_request(Object(), sr, {})[0]
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
        "created": "2026-01-01T00:00:00Z",
        "modified": "2026-01-01T00:00:00Z",
        "ipp_value": 1.0,
        "name": "Test",
        "observation_type": "NORMAL",
        "proposal": "test",
        "request_group_id": 1,
        "submitter": "test",
    }
    obs = LcoObservation.model_validate(obs_json)
    task = LcoTask.from_observation(Object(), obs, {})

    assert task.name == str(obs.request.id)
    assert isinstance(task.target, SiderealTarget)
    assert task.target.name == "Kochab"


# ── run ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_reports_only_the_final_config_status(mocker, task: LcoTask) -> None:
    """run() leaves ATTEMPTED to update_observation() and reports just the result of each config."""
    from unittest.mock import AsyncMock, MagicMock

    from pyobs.robotic.storage.lco.task import ConfigStatus

    from .helpers import make_observation_archive

    archive = make_observation_archive()
    send_mock = mocker.patch.object(archive, "send_update", AsyncMock())
    script = MagicMock(can_run=AsyncMock(return_value=True))
    mocker.patch.object(LcoTask, "pyobs_model_validate", return_value=script)
    mocker.patch.object(
        LcoTask,
        "_run_script",
        AsyncMock(return_value=ConfigStatus().finish(state="COMPLETED", time_completed=12.0)),
    )

    await task.run(MagicMock(observation_archive=archive))

    send_mock.assert_called_once()
    assert send_mock.call_args[0][1]["state"] == "COMPLETED"
    assert send_mock.call_args[0][1]["summary"]["time_completed"] == 12.0
    assert task.request.configurations[0].state == "COMPLETED"


@pytest.mark.asyncio
async def test_run_reports_not_attempted_if_config_cannot_run(mocker, task: LcoTask) -> None:
    from unittest.mock import AsyncMock, MagicMock

    from .helpers import make_observation_archive

    archive = make_observation_archive()
    send_mock = mocker.patch.object(archive, "send_update", AsyncMock())
    script = MagicMock(can_run=AsyncMock(return_value=False))
    mocker.patch.object(LcoTask, "pyobs_model_validate", return_value=script)
    run_script = mocker.patch.object(LcoTask, "_run_script", AsyncMock())

    await task.run(MagicMock(observation_archive=archive))

    run_script.assert_not_called()
    send_mock.assert_called_once()
    assert send_mock.call_args[0][1]["state"] == "NOT_ATTEMPTED"
    assert send_mock.call_args[0][1]["summary"]["reason"] == "Cannot run config."
    assert task.request.configurations[0].state == "NOT_ATTEMPTED"
