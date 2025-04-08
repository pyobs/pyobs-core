from __future__ import annotations
import datetime
from typing import Any, Union, Optional, Dict
from unittest.mock import AsyncMock

import pandas as pd
import pytest
import pytest_mock
from astroplan import Observer

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


class MockPointingSeriesIterator:
    def __init__(self) -> None:
        self.grid_points = pd.DataFrame()
        self.counter = None

    def set_grid_points(self, grid_points: pd.DataFrame) -> None:
        self.grid_points = grid_points

    def __aiter__(self) -> MockPointingSeriesIterator:
        self.counter = len(self.grid_points)
        return self

    async def __anext__(self) -> Optional[Dict[str, Any]]:
        self.counter -= 1
        if self.counter >= 0:
            return {"datetime": "", "ra": 0.0, "dec": 0.0, "az": 0.0, "alt": 0.0}
        raise StopAsyncIteration


@pytest.mark.asyncio
async def test_open(observer: Observer, mocker: pytest_mock.MockerFixture) -> None:
    mocker.patch("pyobs.modules.Module.open")
    mock_proxy = MockProxy()
    mock_proxy.telescope.move_radec = AsyncMock()  # type: ignore

    series = PointingSeries(num_alt=1, num_az=1, observer=observer, finish=0)
    series.comm.proxy = mock_proxy  # type: ignore

    await series.open()

    assert series._pointing_series_iterator._acquisition == mock_proxy.acquisition  # type: ignore
    assert series._pointing_series_iterator._telescope == mock_proxy.telescope  # type: ignore


@pytest.mark.asyncio
async def test_run_thread(observer: Observer, mocker: pytest_mock.MockFixture) -> None:
    current_time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))

    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)
    series = PointingSeries(num_alt=1, num_az=1, observer=observer, finish=0)
    series._pointing_series_iterator = MockPointingSeriesIterator()  # type: ignore
    series._process_acquisition = AsyncMock()  # type: ignore

    await series._run_thread()

    series._process_acquisition.assert_called_once_with(**{"datetime": "", "ra": 0.0, "dec": 0.0, "az": 0.0, "alt": 0.0})


@pytest.mark.asyncio
async def test_no_observer() -> None:
    with pytest.raises(ValueError):
        PointingSeries(num_alt=1, num_az=1, finish=0)


@pytest.mark.asyncio
async def test_is_running(observer: Observer) -> None:
    series = PointingSeries(num_alt=1, num_az=1, observer=observer, finish=0)
    assert await series.is_running() is True
