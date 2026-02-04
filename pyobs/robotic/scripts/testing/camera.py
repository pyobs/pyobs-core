from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from pyobs.interfaces import IWindow

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class CameraTest(Script):
    """Test script for a camera module."""

    camera: str

    async def can_run(self, data: TaskData) -> bool:
        try:
            await self.__comm(data).proxy(self.camera)
            return True
        except ValueError:
            return False

    async def run(self, data: TaskData) -> None:
        proxy = await self.__comm(data).proxy(self.camera, IWindow)
        wnd = await proxy.get_full_frame()
        print(wnd)


__all__ = ["CameraTest"]
