from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import astropy.units as u
import pytest

from pyobs.robotic.observation import Observation, ObservationList
from pyobs.robotic.storage.lco._portal import Portal
from pyobs.robotic.storage.lco._schedulewriter import LcoScheduleWriter
from pyobs.robotic.storage.lco.configdb import ConfigDB
from pyobs.utils.time import Time

from .helpers import make_portal

T0 = Time("2026-06-03T21:25:00", scale="utc")
T1 = Time("2026-06-03T21:28:00", scale="utc")


def make_configdb() -> ConfigDB:
    configdb = MagicMock(spec=ConfigDB)
    instrument = MagicMock()
    instrument.instrument.code = "kb03"
    instrument.instrument.autoguider_camera.code = "ag03"
    configdb.get_instrument_by_type.return_value = [instrument]
    return configdb


def make_writer(portal: Portal | None = None, configdb: ConfigDB | None = None) -> LcoScheduleWriter:
    writer = LcoScheduleWriter.__new__(LcoScheduleWriter)
    writer._comm = None
    writer._observer = None
    writer._vfs = None
    writer._timezone = None
    writer._location = None
    writer._portal = portal or make_portal()
    writer._configdb = configdb or make_configdb()
    writer._site = "goe"
    writer._enclosure = "roof"
    writer._telescope = "0m5a"
    writer._period = 24.0
    return writer


def make_lco_observation() -> Observation:
    from pyobs.robotic.storage.lco._portal import LcoRequest
    from pyobs.robotic.storage.lco.task import LcoTask

    from .conftest import OBSERVATIONS_RESPONSE

    obs_data = OBSERVATIONS_RESPONSE["results"][0]
    request = LcoRequest(**obs_data["request"])
    task = MagicMock(spec=LcoTask)
    task.request = request
    task.name = "Test"
    task.id = 1
    return Observation(task=task, start=T0, end=T1)


# ── _create_observations ──────────────────────────────────────────────────────


def test_create_observations_basic_structure() -> None:
    writer = make_writer()
    obs = make_lco_observation()
    result = writer._create_observations(ObservationList([obs]))

    assert len(result) == 1
    assert result[0]["site"] == "goe"
    assert result[0]["enclosure"] == "roof"
    assert result[0]["telescope"] == "0m5a"
    assert result[0]["request"] == 98260


def test_create_observations_sets_start_end() -> None:
    writer = make_writer()
    obs = make_lco_observation()
    result = writer._create_observations(ObservationList([obs]))

    assert result[0]["start"] == T0.isot
    assert result[0]["end"] == T1.isot


def test_create_observations_adds_configuration_statuses() -> None:
    writer = make_writer()
    obs = make_lco_observation()
    result = writer._create_observations(ObservationList([obs]))

    statuses = result[0]["configuration_statuses"]
    assert len(statuses) == 1
    assert statuses[0]["instrument_name"] == "kb03"
    assert statuses[0]["guide_camera_name"] == "ag03"
    assert statuses[0]["configuration"] == 98262


def test_create_observations_skips_unknown_instrument_type(caplog) -> None:
    configdb = MagicMock(spec=ConfigDB)
    configdb.get_instrument_by_type.return_value = []
    writer = make_writer(configdb=configdb)
    obs = make_lco_observation()

    import logging

    with caplog.at_level(logging.WARNING):
        result = writer._create_observations(ObservationList([obs]))

    assert result[0]["configuration_statuses"] == []
    assert "not found" in caplog.text


def test_create_observations_warns_on_multiple_instruments(caplog) -> None:
    configdb = MagicMock(spec=ConfigDB)
    inst1 = MagicMock()
    inst1.instrument.code = "kb03"
    inst1.instrument.autoguider_camera.code = "ag03"
    inst2 = MagicMock()
    inst2.instrument.code = "kb04"
    configdb.get_instrument_by_type.return_value = [inst1, inst2]
    writer = make_writer(configdb=configdb)
    obs = make_lco_observation()

    import logging

    with caplog.at_level(logging.WARNING):
        result = writer._create_observations(ObservationList([obs]))

    assert "More than one instrument" in caplog.text
    assert result[0]["configuration_statuses"][0]["instrument_name"] == "kb03"


def test_create_observations_empty_list() -> None:
    writer = make_writer()
    result = writer._create_observations(ObservationList())
    assert result == []


def test_create_observations_multiple_tasks() -> None:
    writer = make_writer()
    obs1 = make_lco_observation()
    obs2 = make_lco_observation()
    result = writer._create_observations(ObservationList([obs1, obs2]))
    assert len(result) == 2


# ── add_schedule / clear_schedule ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_schedule_calls_portal() -> None:
    portal = make_portal()
    portal.submit_observations = AsyncMock()
    writer = make_writer(portal=portal)
    obs = make_lco_observation()

    await writer.add_schedule(ObservationList([obs]))
    portal.submit_observations.assert_called_once()


@pytest.mark.asyncio
async def test_clear_schedule_calls_portal() -> None:
    portal = make_portal()
    portal.clear_schedule = AsyncMock()
    writer = make_writer(portal=portal)

    await writer.clear_schedule(T0)
    portal.clear_schedule.assert_called_once()
    args = portal.clear_schedule.call_args[0]
    assert args[0] == T0
    # end should be T0 + period hours
    assert abs((args[1] - T0).to(u.hour).value - writer._period) < 0.001
