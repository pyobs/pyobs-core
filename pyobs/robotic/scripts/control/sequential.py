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
        if self.check_all_can_run:
            results = [await s.can_run(data) for s in self.scripts]
            can_run = all(results)
            reasons = filter(lambda s: s is not None, [s.cant_run_reason() for s in self.scripts])
            self._cant_run_reason = None if can_run else "Reason(s): " + " ".join(reasons)
        else:
            can_run = await self.scripts[0].can_run(data)
            self._cant_run_reason = self.scripts[0].cant_run_reason()
        return can_run

    async def run(self, data: TaskData | None) -> None:
        for script in self.scripts:
            if await script.can_run(data):
                await script.run(data)
            else:
                log.info("Script %s cannot run.", script.__class__.__name__)


__all__ = ["SequentialRunner"]
