from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm import Comm
from pyobs.interfaces import IPointingAltAz
from pyobs.modules.flatfield.pointing import FlatFieldPointing
from pyobs.robotic.utils.skyflats.pointing.base import SkyFlatsBasePointing
from tests.helpers import make_proxy_cm


def make_pointing_module(pointing: AsyncMock) -> FlatFieldPointing:
    comm = MagicMock(spec=Comm)
    return FlatFieldPointing(telescope="telescope", pointing=pointing, comm=comm)


@pytest.mark.asyncio
async def test_run_points_telescope() -> None:
    pointing = AsyncMock(spec=SkyFlatsBasePointing)
    module = make_pointing_module(pointing)
    telescope = MagicMock(spec=IPointingAltAz)
    module._comm.proxy = MagicMock(return_value=make_proxy_cm(telescope))

    await module.run()

    assert pointing.await_count == 1
    assert pointing.await_args.args == (telescope,)


@pytest.mark.asyncio
async def test_abort_is_noop() -> None:
    pointing = AsyncMock(spec=SkyFlatsBasePointing)
    module = make_pointing_module(pointing)

    # should not raise
    await module.abort()
