from __future__ import annotations
import asyncio
import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script


log = logging.getLogger(__name__)


class ParallelRunner(Script):
    """Script for running other scripts in parallel."""

    scripts: list[dict[str, Any]]
    check_all_can_run: bool = True

    async def can_run(self, data: TaskData) -> bool:
        check_all = [await Script.model_validate(s).can_run(data) for s in self.scripts]
        return all(check_all) if self.check_all_can_run else any(check_all)

    async def run(self, data: TaskData) -> None:
        scripts = [Script.model_validate(s) for s in self.scripts]
        tasks = [asyncio.create_task(self._run_script(s, data)) for s in scripts if await s.can_run(data)]
        await asyncio.gather(*tasks)

    async def _run_script(self, script: Script, data: TaskData) -> None:
        try:
            await script.run(data)
        except:
            log.exception("Script failed.")


__all__ = ["ParallelRunner"]
