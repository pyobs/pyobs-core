from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.comm import Comm
from pyobs.comm.proxy import Proxy
from pyobs.interfaces import IBinning, IWindow
from pyobs.interfaces.IWindow import WindowCapabilities
from pyobs.mixins.camerasettings import CameraSettingsMixin
from pyobs.modules import Module


class SettingsModule(Module, CameraSettingsMixin):
    """Minimal concrete module for exercising CameraSettingsMixin in isolation."""

    def __init__(self, **kwargs) -> None:
        Module.__init__(self, **kwargs)
        CameraSettingsMixin.__init__(self, **kwargs)


def make_module(**kwargs) -> SettingsModule:
    comm = MagicMock(spec=Comm)
    return SettingsModule(comm=comm, **kwargs)


def make_camera_proxy(interfaces: list) -> tuple[Proxy, MagicMock]:
    comm = MagicMock()
    comm.cast_to_simple_pre = []
    comm.cast_to_simple_post = []
    comm.execute = AsyncMock(return_value=None)
    proxy = Proxy(comm, "camera", interfaces)
    return proxy, comm


CAPS = WindowCapabilities(full_frame_x=0, full_frame_y=0, full_frame_width=2048, full_frame_height=2048)


@pytest.mark.asyncio
async def test_sets_window_to_full_frame_once_capabilities_arrive_late() -> None:
    """Capabilities for a Proxy are fetched in the background (see Comm._fetch_and_update_capabilities);
    _do_camera_settings must wait for that fetch instead of only checking the not-yet-populated cache."""
    m = make_module()
    camera, comm = make_camera_proxy([IWindow])

    async def deliver_late() -> None:
        await asyncio.sleep(0.05)
        camera.update_capabilities(IWindow, CAPS)

    asyncio.ensure_future(deliver_late())

    await m._do_camera_settings(camera)

    comm.execute.assert_awaited_once()
    call_args = comm.execute.await_args.args
    assert call_args[0:2] == ("camera", "set_window")
    assert call_args[3:] == (0, 0, 2048, 2048)


@pytest.mark.asyncio
async def test_raises_when_capabilities_never_arrive(monkeypatch) -> None:
    m = make_module()
    camera, _ = make_camera_proxy([IWindow])

    # avoid a real 10s wait for the background fetch that will never deliver anything
    async def fake_wait_for(coro, timeout):
        coro.close()
        raise TimeoutError

    monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)

    with pytest.raises(ValueError, match="Could not get full frame size."):
        await m._do_camera_settings(camera)


@pytest.mark.asyncio
async def test_sets_binning_before_window() -> None:
    m = make_module(binning=2)
    camera, comm = make_camera_proxy([IWindow, IBinning])
    camera.update_capabilities(IWindow, CAPS)

    await m._do_camera_settings(camera)

    binning_calls = [c for c in comm.execute.await_args_list if c.args[1] == "set_binning"]
    assert len(binning_calls) == 1
    assert binning_calls[0].args[3:] == (2, 2)
