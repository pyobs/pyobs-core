"""Integration test for #1030: a domain exception raised in a remote call must reach the caller
over real XMPP as its own type with its message, not as an empty RemoteError.

Requires a live ejabberd server -- see tests/xmpp/docker-compose.yml.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from pyobs.interfaces import ICooling
from pyobs.modules.camera.dummycamera import DummyCamera
from pyobs.utils import exceptions as exc

pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.xmpp]


class _FailingCamera(DummyCamera):
    async def set_cooling(self, enabled: bool, setpoint: float, **kwargs: Any) -> None:
        raise exc.InitError("Startup of telescope was interrupted.")


async def _wait_for(condition, *, timeout: float = 15.0) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        if condition():
            return True
        await asyncio.sleep(0.1)
    return False


async def test_init_error_reaches_caller(make_xmpp_comm, make_camera_comm) -> None:
    async def _run() -> None:
        camera = _FailingCamera(comm=make_camera_comm)
        try:
            await camera.startup()
            observer_comm = await make_xmpp_comm("observer")
            assert await _wait_for(lambda: "camera" in observer_comm.clients)

            async with observer_comm.proxy("camera", ICooling) as cam:
                with pytest.raises(exc.InitError) as exc_info:
                    await cam.set_cooling(enabled=True, setpoint=-20.0)
            assert exc_info.value.message == "Startup of telescope was interrupted."
        finally:
            await camera.close()

    await asyncio.wait_for(_run(), timeout=60)
