from __future__ import annotations
import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class CallModule(Script):
    """Script for calling method on a module."""

    module: str
    method: str
    params: list[Any] | None = [None]

    async def can_run(self, data: TaskData) -> bool:
        try:
            await self.__comm(data).proxy(self.module)
            return True
        except ValueError:
            return False

    async def run(self, data: TaskData) -> None:
        proxy = await self.__comm(data).proxy(self.module)
        await proxy.execute(self.method, *self.params)


__all__ = ["CallModule"]
