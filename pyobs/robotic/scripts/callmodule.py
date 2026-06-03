from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class CallModule(Script):
    """Script for calling method on a module."""

    module: str
    method: str
    params: list[str | int | float] = Field(default_factory=list)

    async def can_run(self, data: TaskData | None) -> bool:
        try:
            await self.comm.proxy(self.module)
            return True
        except ValueError:
            return False

    async def run(self, data: TaskData | None) -> None:
        proxy = await self.comm.proxy(self.module)
        await proxy.execute(self.method, *self.params)


__all__ = ["CallModule"]
