import datetime
from typing import Any, Union
from unittest.mock import AsyncMock

import pytest

import pyobs
from pyobs.modules.robotic import PointingSeries
from tests.modules.robotic.conftest import MockAcquisition, MockTelescope


class MockProxy:
    def __init__(self, **kwargs: Any) -> None:
        self.acquisition = MockAcquisition()
        self.telescope = MockTelescope()

    async def __call__(self, name: str, *args: Any, **kwargs: Any) -> Union[MockTelescope, MockAcquisition]:
        if name == "acquisition":
            return self.acquisition
        if name == "telescope":
            return self.telescope

        raise ValueError


@pytest.mark.asyncio
async def test_run_thread(observer, mocker):
    mock_proxy = MockProxy()
    mock_proxy.telescope.move_radec = AsyncMock()  # type: ignore

    current_time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))

    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)
    series = PointingSeries(num_alt=1, num_az=1, observer=observer, finish=0)
    series.comm.proxy = mock_proxy  # type: ignore
    series._process_acquisition = AsyncMock()  # type: ignore

    await series.open()
    await series._run_thread()

    mock_proxy.telescope.move_radec.assert_called_once_with(151.12839530803322, 27.74121078725986)
    series._process_acquisition.assert_called_once_with(**{"datetime": "", "ra": 0.0, "dec": 0.0, "az": 0.0, "alt": 0.0})
