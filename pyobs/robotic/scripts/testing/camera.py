from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyobs.interfaces import IWindow

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class CameraTestScript(Script):
    """Test script for a camera module."""

    camera: str

    async def can_run(self, data: TaskData | None) -> bool:
        try:
            await self.comm.proxy(self.camera)
            return True
        except ValueError:
            return False

    async def run(self, data: TaskData | None) -> None:
        proxy = await self.comm.proxy(self.camera, IWindow)
        wnd = await proxy.get_full_frame()
        print(wnd)


__all__ = ["CameraTestScript"]
