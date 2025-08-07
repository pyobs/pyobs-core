from typing import Optional, Any
from unittest.mock import AsyncMock

import pytest

import pyobs
from pyobs.modules.roof import BaseRoof
from pyobs.utils.enums import MotionStatus


class MockBaseRoof(BaseRoof):
    async def init(self, **kwargs: Any) -> None:
        pass

    async def park(self, **kwargs: Any) -> None:
        pass

    async def stop_motion(self, device: Optional[str] = None, **kwargs: Any) -> None:
        pass


@pytest.mark.asyncio
async def test_open(mocker):
    mocker.patch("pyobs.mixins.WeatherAwareMixin.open")
    mocker.patch("pyobs.mixins.MotionStatusMixin.open")
    mocker.patch("pyobs.modules.Module.open")

    telescope = MockBaseRoof()
    await telescope.open()

    pyobs.mixins.WeatherAwareMixin.open.assert_called_once_with(telescope)
    pyobs.mixins.MotionStatusMixin.open.assert_called_once_with(telescope)
    pyobs.modules.Module.open.assert_called_once_with(telescope)


@pytest.mark.asyncio
async def test_get_fits_header_before_open():
    telescope = MockBaseRoof()

    telescope.get_motion_status = AsyncMock(return_value=MotionStatus.POSITIONED)
    header = await telescope.get_fits_header_before()

    assert header["ROOF-OPN"] == (True, "True for open, false for closed roof")


@pytest.mark.asyncio
async def test_get_fits_header_before_closed():
    telescope = MockBaseRoof()

    telescope.get_motion_status = AsyncMock(return_value=MotionStatus.PARKED)
    header = await telescope.get_fits_header_before()

    assert header["ROOF-OPN"] == (False, "True for open, false for closed roof")


@pytest.mark.asyncio
async def test_ready():
    telescope = MockBaseRoof()

    telescope.get_motion_status = AsyncMock(return_value=MotionStatus.TRACKING)
    assert await telescope.is_ready() is True


@pytest.mark.asyncio
async def test_not_ready():
    telescope = MockBaseRoof()

    telescope.get_motion_status = AsyncMock(return_value=MotionStatus.PARKING)
    assert await telescope.is_ready() is False
