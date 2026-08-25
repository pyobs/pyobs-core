from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class LogScript(Script):
    """Script for logging something."""

    expression: str = Field(description="Python expression to evaluate and log the value of.")

    async def can_run(self, data: TaskData | None) -> bool:
        return True

    async def run(self, data: TaskData | None) -> None:
        # evaluate condition
        value = eval(self.expression, {"now": datetime.now(UTC)})

        # log it
        log.info(value)


__all__ = ["LogScript"]
