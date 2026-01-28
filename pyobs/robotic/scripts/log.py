from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic import TaskRunner, ObservationArchive, TaskArchive
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class LogRunner(Script):
    """Script for logging something."""

    __module__ = "pyobs.modules.robotic"

    def __init__(
        self,
        expression: str,
        **kwargs: Any,
    ):
        """Initialize a new LogRunner.

        Args:
            expression: expression to check
        """
        Script.__init__(self, **kwargs)
        self.expression = expression

    async def can_run(self) -> bool:
        return True

    async def run(
        self,
        task_runner: TaskRunner | None = None,
        observation_archive: ObservationArchive | None = None,
        task_archive: TaskArchive | None = None,
    ) -> None:
        # evaluate condition
        value = eval(self.expression, {"now": datetime.now(timezone.utc), "config": self.configuration})

        # log it
        log.info(value)


__all__ = ["LogRunner"]
