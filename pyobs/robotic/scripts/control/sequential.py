from __future__ import annotations
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class SequentialRunner(Script):
    """Script for running a sequence of other scripts."""

    scripts: list[Script]
    check_all_can_run: bool = True

    async def can_run(self, data: TaskData | None) -> bool:
        results = [await s.can_run(data) for s in self.scripts]
        return all(results) if self.check_all_can_run else results[0]

    async def run(self, data: TaskData | None) -> None:
        for script in self.scripts:
            if await script.can_run(data):
                await script.run(data)
            else:
                log.info("Script %s cannot run.", script.__class__.__name__)


__all__ = ["SequentialRunner"]
