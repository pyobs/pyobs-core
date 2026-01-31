from __future__ import annotations
import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class SequentialRunner(Script):
    """Script for running a sequence of other scripts."""

    scripts: list[dict[str, Any]]
    check_all_can_run: bool = True

    async def can_run(self, data: TaskData) -> bool:
        check_all = [await self.get_object(s, Script).can_run() for s in self.scripts]
        return all(check_all) if self.check_all_can_run else check_all[0]

    async def run(self, data: TaskData) -> None:
        for s in self.scripts:
            script = Script.model_validate(s)
            if await script.can_run(data):
                await script.run(data)
            else:
                log.info(f"Script {s['class']} cannot run.")


__all__ = ["SequentialRunner"]
