from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class ConditionalRunner(Script):
    """Script for running an if condition."""

    condition: str
    true: Script
    false: Script | None = None

    def __get_script(self) -> Script | None:
        # evaluate condition
        ret = eval(self.condition, {"now": datetime.now(UTC)})

        # run scripts
        if ret:
            return self.true
        elif self.false is not None:
            return self.false
        else:
            return None

    async def can_run(self, data: TaskData | None) -> bool:
        script = self.__get_script()
        can_run = True if script is None else await script.can_run(data)
        self._cant_run_reason = script.cant_run_reason() if script is not None else None
        return can_run

    async def run(self, data: TaskData | None) -> None:
        script = self.__get_script()
        if script is not None:
            await script.run(data)

    def get_fits_headers(self, namespaces: list[str] | None = None) -> dict[str, Any]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        script = self.__get_script()
        return script.get_fits_headers(namespaces) if script is not None else {}


__all__ = ["ConditionalRunner"]
