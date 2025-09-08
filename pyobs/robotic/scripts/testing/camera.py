from __future__ import annotations
import logging
from typing import Any, TYPE_CHECKING

from pyobs.interfaces import IWindow

if TYPE_CHECKING:
    from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class CameraTest(Script):
    """Test script for a camera module."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        camera: str,
        **kwargs: Any,
    ):
        """Initialize a new camera test script..

        Args:
            camera: name of camera module.
        """
        Script.__init__(self, **kwargs)
        self.camera = camera

    async def can_run(self) -> bool:
        try:
            await self.comm.proxy(self.camera)
            return True
        except ValueError:
            return False

    async def run(
        self,
        task_runner: TaskRunner | None = None,
        task_schedule: TaskSchedule | None = None,
        task_archive: TaskArchive | None = None,
    ) -> None:
        proxy = await self.comm.proxy(self.camera, IWindow)
        wnd = await proxy.get_full_frame()
        print(wnd)


__all__ = ["CameraTest"]
