import json
from typing import Any

import pytest

from pyobs.robotic.storage.lco._portal import Portal

from .test_task import REQUEST_CONFIG


@pytest.mark.asyncio
async def test_schedulable_requests(mocker: Any) -> None:
    request_config = [json.loads(REQUEST_CONFIG)]
    portal = Portal("", "", "", "", "")
    mocker.patch.object(portal, "_get", return_value=request_config)
    schedulable_requests = await portal.schedulable_requests()

    assert len(schedulable_requests) == 1


@pytest.mark.asyncio
async def test_observations_parses_no_request_shape(mocker: Any) -> None:
    """Regression test: GET /api/requests/{id}/observations/ (Portal.observations()) is served by
    the portal's RequestViewSet.observations action, which calls Observation.as_dict(no_request=True)
    - a materially different, sparser shape than GET /api/observations/ (Portal.download_schedule()).
    no_request=True omits created/modified/ipp_value/name/observation_type/proposal/request_group_id/
    submitter entirely (see observation_portal.observations.models.observation_as_dict) and leaves
    `request` as a bare foreign-key id rather than an expanded object. Confirmed against the actual
    portal source, not just pyobs's own test fixtures (which only model the download_schedule shape)."""
    no_request_response = [
        {
            "id": 1020277,
            "request": 98260,
            "site": "goe",
            "enclosure": "roof",
            "telescope": "0m5a",
            "start": "2026-06-03T21:25:26Z",
            "end": "2026-06-03T21:27:57Z",
            "priority": 10,
            "state": "PENDING",
            "configuration_statuses": [],
        }
    ]
    portal = Portal("", "", "", "", "")
    mocker.patch.object(portal, "_get", return_value=no_request_response)
    observations = await portal.observations(98260)

    assert len(observations) == 1
    assert observations[0].id == 1020277
    assert observations[0].request == 98260
    assert observations[0].ipp_value is None
