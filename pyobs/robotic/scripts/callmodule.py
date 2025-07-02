from __future__ import annotations
import logging
from typing import Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class CallModule(Script):
    """Script for calling method on a module."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        module: str,
        method: str,
        params: Optional[List[Any]] = None,
        **kwargs: Any,
    ):
        """Initialize a new SequentialRunner.

        Args:
            script: list or dict of scripts to run in a sequence.
        """
        Script.__init__(self, **kwargs)
        self.module = module
        self.method = method
        self.params = params or []

    async def can_run(self) -> bool:
        try:
            self.comm.proxy(self.module)
            return True
        except ValueError:
            return False

    async def run(
        self,
        task_runner: TaskRunner,
        task_schedule: Optional[TaskSchedule] = None,
        task_archive: Optional[TaskArchive] = None,
    ) -> None:
        proxy = await self.comm.proxy(self.module)
        await proxy.execute(self.method, *self.params)


__all__ = ["CallModule"]
