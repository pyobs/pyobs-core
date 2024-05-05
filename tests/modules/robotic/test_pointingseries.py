import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest

import pyobs
from pyobs.modules.robotic import PointingSeries


class MockAcquisition:
    async def acquire_target(self, **kwargs: Any) -> Dict[str, Any]:
        return {"datetime": "", "ra": 0.0, "dec": 0.0, "az": 0.0, "alt": 0.0}


class MockTelescope:
    async def move_radec(*args, **kwargs):
        pass


class MockProxy:
    def __init__(self, **kwargs):
        self.acquisition = MockAcquisition()
        self.telescope = MockTelescope()

    async def __call__(self, name, *args, **kwargs):
        if name == "acquisition":
            return self.acquisition
        if name == "telescope":
            return self.telescope

        raise ValueError


@pytest.mark.asyncio
async def test_run_thread(observer, mocker):
    mock_proxy = MockProxy()
    mock_proxy.telescope.move_radec = AsyncMock()

    current_time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))

    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)
    series = PointingSeries(num_alt=1, num_az=1, observer=observer, finish=1)
    series.comm.proxy = mock_proxy
    series._process_acquisition = AsyncMock()
    await series._run_thread()

    mock_proxy.telescope.move_radec.assert_called_once_with(151.12839530803322, 27.74121078725986)
    series._process_acquisition.assert_called_once_with(**{"datetime": "", "ra": 0.0, "dec": 0.0, "az": 0.0, "alt": 0.0})
