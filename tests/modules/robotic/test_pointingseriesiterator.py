import datetime
from unittest.mock import AsyncMock

import astroplan
import pandas as pd
import pytest
import pytest_mock
from astropy.coordinates import SkyCoord

import pyobs
from pyobs.modules.robotic._pointingseriesiterator import _PointingSeriesIterator
from tests.modules.robotic.conftest import MockTelescope, MockAcquisition


@pytest.mark.asyncio
async def test_empty(observer: astroplan.Observer) -> None:
    coords = pd.DataFrame({"alt": [], "az": [], "done": []})
    coords.set_index(["alt", "az"])

    iterator = _PointingSeriesIterator(observer,
                                       MockTelescope(),  # type: ignore
                                       MockAcquisition(),  # type: ignore
                                       (-80.0, 80.0), 1, 0, coords)

    with pytest.raises(StopAsyncIteration):
        await anext(iterator)  # type: ignore


@pytest.mark.asyncio
async def test_next(observer: astroplan.Observer, mocker: pytest_mock.MockerFixture) -> None:
    current_time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))

    mocker.patch("astropy.coordinates.SkyCoord.transform_to", return_value=SkyCoord(0, 0, unit='deg', frame='icrs'))
    mocker.patch("astroplan.Observer.moon_altaz", return_value=SkyCoord(-90, 0, unit='deg', frame='altaz', obstime=current_time, location=observer.location))

    coords = pd.DataFrame({"alt": [60], "az": [0], "done": [False]})
    coords = coords.set_index(["alt", "az"])

    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)

    iterator = _PointingSeriesIterator(observer,
                                       MockTelescope(),     # type: ignore
                                       MockAcquisition(),   # type: ignore
                                       (-80.0, 80.0), 1, 0, coords)

    iterator._telescope.move_radec = AsyncMock()  # type: ignore

    assert await anext(iterator) == {"datetime": "", "ra": 0.0, "dec": 0.0, "az": 0.0, "alt": 0.0}  # type: ignore

    iterator._telescope.move_radec.assert_called_once_with(0, 0)


@pytest.mark.asyncio
async def test_acquire_error(observer: astroplan.Observer, mocker: pytest_mock.MockerFixture) -> None:
    current_time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))

    mocker.patch("astropy.coordinates.SkyCoord.transform_to", return_value=SkyCoord(0, 0, unit='deg', frame='icrs'))
    mocker.patch("astroplan.Observer.moon_altaz", return_value=SkyCoord(-90, 0, unit='deg', frame='altaz', obstime=current_time, location=observer.location))

    coords = pd.DataFrame({"alt": [60], "az": [0], "done": [False]})
    coords = coords.set_index(["alt", "az"])

    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)

    iterator = _PointingSeriesIterator(observer,
                                       MockTelescope(),     # type: ignore
                                       MockAcquisition(),   # type: ignore
                                       (-80.0, 80.0), 1, 0, coords)

    iterator._acquisition.acquire_target = AsyncMock(side_effect=ValueError)  # type: ignore

    assert await anext(iterator) is None  # type: ignore

