import json
from typing import Any

import pytest

from pyobs.robotic.lco._portal import Portal
from .test_task import REQUEST_CONFIG


@pytest.mark.asyncio
async def test_schedulable_requests(mocker: Any) -> None:
    request_config = [json.loads(REQUEST_CONFIG)]
    portal = Portal("", "", "", "", "")
    mocker.patch.object(portal, "_get", return_value=request_config)
    schedulable_requests = await portal.schedulable_requests()

    assert len(schedulable_requests) == 1
