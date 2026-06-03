from __future__ import annotations
import pytest
from unittest.mock import AsyncMock

from pyobs.robotic.lco._portal import LcoSchedulableRequest, LcoObservation
from pyobs.robotic.lco.task import LcoTask
from pyobs.robotic.observation import ObservationState
from pyobs.utils.time import Time
from .conftest import (
    SCHEDULABLE_REQUESTS_RESPONSE,
    OBSERVATIONS_RESPONSE,
    CONFIG_STATUS_RESPONSE,
)
from .helpers import make_task_archive, make_observation_archive


def make_lco_task() -> LcoTask:
    sr = LcoSchedulableRequest.model_validate(SCHEDULABLE_REQUESTS_RESPONSE[0])
    return LcoTask.from_schedulable_request(sr, {})[0]


# ── LcoTaskArchive ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_task_archive_get_schedulable_tasks(mocker) -> None:
    """get_schedulable_tasks returns PENDING tasks filtered by instrument."""
    archive = make_task_archive()

    sr = LcoSchedulableRequest.model_validate(SCHEDULABLE_REQUESTS_RESPONSE[0])
    mocker.patch.object(archive._portal, "schedulable_requests", AsyncMock(return_value=[sr]))
    mocker.patch.object(archive._portal, "proposals", AsyncMock(return_value=[{"id": "test", "tac_priority": 1.0}]))

    tasks = await archive.get_schedulable_tasks()
    assert len(tasks) == 1
    assert tasks[0].name == "Test"


@pytest.mark.asyncio
async def test_task_archive_filters_by_instrument(mocker) -> None:
    """Tasks with non-matching instrument type are excluded."""
    archive = make_task_archive(instrument_type="some_other_instrument")

    sr = LcoSchedulableRequest.model_validate(SCHEDULABLE_REQUESTS_RESPONSE[0])
    mocker.patch.object(archive._portal, "schedulable_requests", AsyncMock(return_value=[sr]))
    mocker.patch.object(archive._portal, "proposals", AsyncMock(return_value=[{"id": "test", "tac_priority": 1.0}]))

    tasks = await archive.get_schedulable_tasks()
    assert len(tasks) == 0


@pytest.mark.asyncio
async def test_task_archive_excludes_non_pending_requests(mocker) -> None:
    """Tasks with non-PENDING request state are excluded — only PENDING requests need scheduling."""
    import copy

    data = copy.deepcopy(SCHEDULABLE_REQUESTS_RESPONSE[0])
    data["requests"][0]["state"] = "COMPLETED"

    archive = make_task_archive()
    sr = LcoSchedulableRequest.model_validate(data)
    mocker.patch.object(archive._portal, "schedulable_requests", AsyncMock(return_value=[sr]))
    mocker.patch.object(archive._portal, "proposals", AsyncMock(return_value=[{"id": "test", "tac_priority": 1.0}]))

    tasks = await archive.get_schedulable_tasks()
    assert len(tasks) == 0


@pytest.mark.asyncio
async def test_task_archive_last_changed(mocker) -> None:
    archive = make_task_archive()
    mocker.patch.object(archive._portal, "last_changed", AsyncMock(return_value=Time("2026-05-27T08:18:50Z")))

    t = await archive.last_changed()
    assert t is not None
    assert t.isot.startswith("2026-05-27")


@pytest.mark.asyncio
async def test_task_archive_last_changed_returns_cached_on_error(mocker) -> None:
    """last_changed returns last known time if portal call fails."""
    archive = make_task_archive()
    archive._last_changed = Time("2026-05-26T00:00:00Z")

    mocker.patch.object(archive._portal, "last_changed", AsyncMock(side_effect=RuntimeError("portal down")))

    t = await archive.last_changed()
    assert t is not None
    assert t.isot.startswith("2026-05-26")


# ── LcoObservationArchive ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_observation_archive_get_observations(mocker) -> None:
    archive = make_observation_archive()
    task = make_lco_task()

    obs_list = [LcoObservation.model_validate(OBSERVATIONS_RESPONSE["results"][0])]
    mocker.patch.object(archive._portal, "observations", AsyncMock(return_value=obs_list))

    result = await archive.get_observations(task=task)
    assert len(result) == 1
    assert result[0].state == ObservationState.PENDING
    assert result[0].task is task


@pytest.mark.asyncio
async def test_observation_archive_get_observations_requires_lco_task() -> None:
    from pyobs.robotic import Task

    archive = make_observation_archive()
    task = Task(id="plain", name="plain", duration=100)

    with pytest.raises(ValueError, match="not a LCO task"):
        await archive.get_observations(task=task)


@pytest.mark.asyncio
async def test_observation_archive_get_observations_state_filter(mocker) -> None:
    archive = make_observation_archive()
    task = make_lco_task()

    obs_list = [LcoObservation.model_validate(OBSERVATIONS_RESPONSE["results"][0])]
    mocker.patch.object(archive._portal, "observations", AsyncMock(return_value=obs_list))

    completed = await archive.get_observations(task=task, state=ObservationState.COMPLETED)
    assert len(completed) == 0

    pending = await archive.get_observations(task=task, state=ObservationState.PENDING)
    assert len(pending) == 1


@pytest.mark.asyncio
async def test_observation_archive_send_update(mocker) -> None:
    archive = make_observation_archive()
    patch_mock = mocker.patch.object(
        archive._portal, "update_configuration_status", AsyncMock(return_value=CONFIG_STATUS_RESPONSE)
    )

    await archive.send_update(1020277, {"state": "COMPLETED", "summary": {}})
    patch_mock.assert_called_once_with(1020277, {"state": "COMPLETED", "summary": {}})


@pytest.mark.asyncio
async def test_observation_archive_send_update_skips_none() -> None:
    archive = make_observation_archive()
    archive._portal.update_configuration_status = AsyncMock()

    await archive.send_update(None, {"state": "COMPLETED"})
    archive._portal.update_configuration_status.assert_not_called()


# ── ConfigDB ──────────────────────────────────────────────────────────────────

# ── ConfigDB ──────────────────────────────────────────────────────────────────


def test_configdb_get_instrument_by_type() -> None:
    """ConfigDB.get_instrument_by_type filters by site/enclosure/telescope/type."""
    from pyobs.robotic.lco.configdb import (
        ConfigDB,
        Site,
        Enclosure,
        Telescope,
        Instrument,
        Camera,
        CameraType,
        InstrumentType,
    )

    camera_type = CameraType(id=1, size="", pscale=0.0, name="", code="kb03", pixels_x=3072, pixels_y=2048, max_rois=1)
    camera = Camera(
        id=1, code="kb03", camera_type=camera_type, orientation=0.0, optical_element_groups=[], host="localhost"
    )
    instrument_type = InstrumentType(
        id=1,
        name="SBIG 6303e",
        code="0M5 IAG50CM SBIG6303E",
        fixed_overhead_per_exposure=0.0,
        instrument_category="IMAGE",
        observation_front_padding=0.0,
        acquire_exposure_time=0.0,
        default_configuration_type="EXPOSE",
        mode_types=[],
        default_acceptability_threshold=90.0,
        config_front_padding=0.0,
        allow_self_guiding=False,
        configuration_types=[],
        validation_schema={},
    )
    instrument = Instrument(
        id=1,
        code="kb03",
        state="SCHEDULABLE",
        telescope="0m5a",
        autoguider_camera=camera,
        science_cameras=[camera],
        instrument_type=instrument_type,
    )
    telescope = Telescope(
        id=1,
        serial_number="",
        name="0m5a",
        code="0m5a",
        active=True,
        aperture=0.5,
        lat=0.0,
        slew_rate=0.0,
        minimum_slew_overhead=0.0,
        instrument_change_overhead=0.0,
        long=0.0,
        enclosure="roof",
        horizon=30.0,
        ha_limit_pos=4.5,
        ha_limit_neg=-4.5,
        telescope_front_padding=0.0,
        zenith_blind_spot=0.0,
        instrument_set=[instrument],
    )
    enclosure = Enclosure(id=1, name="roof", code="roof", active=True, site="goe", telescope_set=[telescope])
    site = Site(
        id=1,
        name="Goettingen",
        code="goe",
        active=True,
        timezone=1,
        restart="",
        tz="Europe/Berlin",
        lat=51.56,
        long=9.94,
        enclosure_set=[enclosure],
    )

    configdb = ConfigDB.__new__(ConfigDB)
    configdb.config = [site]

    result = configdb.get_instrument_by_type("0M5 IAG50CM SBIG6303E", site="goe", enclosure="roof", telescope="0m5a")
    assert len(result) == 1
    assert result[0].instrument.code == "kb03"

    # wrong site
    assert len(configdb.get_instrument_by_type("0M5 IAG50CM SBIG6303E", site="saao")) == 0

    # wrong instrument type
    assert len(configdb.get_instrument_by_type("OTHER_INSTRUMENT", site="goe", enclosure="roof", telescope="0m5a")) == 0


# ── new abstract method implementations ───────────────────────────────────────


@pytest.mark.asyncio
async def test_task_archive_get_projects(mocker) -> None:
    """get_projects maps LCO proposals to Project objects."""
    archive = make_task_archive()
    mocker.patch.object(
        archive._portal,
        "proposals",
        AsyncMock(
            return_value=[
                {"id": "test", "tac_priority": 2.0},
                {"id": "other", "tac_priority": 1.0},
            ]
        ),
    )

    projects = await archive.get_projects()
    assert len(projects) == 2
    codes = {p.code for p in projects}
    assert "test" in codes
    assert "other" in codes
    test_project = next(p for p in projects if p.code == "test")
    assert test_project.priority == 2.0


@pytest.mark.asyncio
async def test_task_archive_get_task_found(mocker) -> None:
    """get_task returns task when found in cache."""
    archive = make_task_archive()
    task = make_lco_task()
    archive._tasks = {str(task.id): task}

    result = await archive.get_task(task.id)
    assert result is task


@pytest.mark.asyncio
async def test_task_archive_get_task_not_found() -> None:
    """get_task returns None when task not in cache."""
    archive = make_task_archive()
    archive._tasks = {}

    result = await archive.get_task(99999)
    assert result is None


@pytest.mark.asyncio
async def test_observation_archive_update_observation(mocker) -> None:
    """update_observation sends config status update to portal."""
    from pyobs.robotic.observation import Observation, ObservationState
    from pyobs.utils.time import Time

    archive = make_observation_archive()
    task = make_lco_task()
    obs = Observation(task=task, start=Time.now(), end=Time.now(), state=ObservationState.COMPLETED)

    send_mock = mocker.patch.object(archive, "send_update", AsyncMock())
    await archive.update_observation(obs)

    # should call send_update for each configuration
    assert send_mock.call_count == len(task.request.configurations)
    # status_id should match configuration_status
    call_args = send_mock.call_args_list[0]
    assert call_args[0][0] == task.request.configurations[0].configuration_status


@pytest.mark.asyncio
async def test_observation_archive_update_observation_skips_non_lco(mocker) -> None:
    """update_observation is a no-op for non-LCO tasks."""
    from pyobs.robotic import Task
    from pyobs.robotic.observation import Observation, ObservationState
    from pyobs.utils.time import Time

    archive = make_observation_archive()
    task = Task(id="plain", name="plain", duration=100)
    obs = Observation(task=task, start=Time.now(), end=Time.now(), state=ObservationState.COMPLETED)

    send_mock = mocker.patch.object(archive, "send_update", AsyncMock())
    await archive.update_observation(obs)
    send_mock.assert_not_called()
