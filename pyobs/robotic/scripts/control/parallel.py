from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


async def _run_script(script: Script, data: TaskData | None) -> None:
    try:
        await script.run(data)
    except Exception:
        log.exception("Script failed.")


class ParallelRunner(Script):
    """Script for running other scripts in parallel."""

    scripts: list[Script]
    check_all_can_run: bool = True

    async def can_run(self, data: TaskData | None) -> bool:
        results = [await s.can_run(data) for s in self.scripts]
        can_run = all(results) if self.check_all_can_run else any(results)
        reasons = [t for t in [s.cant_run_reason() for s in self.scripts] if t is not None]
        self._cant_run_reason = None if can_run else "Reason(s): " + " ".join(reasons)
        return can_run

    async def run(self, data: TaskData | None) -> None:
        async with asyncio.TaskGroup() as tg:
            for s in self.scripts:
                if await s.can_run(data):
                    tg.create_task(_run_script(s, data))


__all__ = ["ParallelRunner"]
