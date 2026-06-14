from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
    from pyobs.utils.time import Time
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class CasesRunner(Script):
    """Script for distinguishing cases."""

    expression: str
    cases: dict[str | int | float, Script]

    def __get_script(self) -> Script:
        # evaluate condition
        value = eval(self.expression, {"now": datetime.now(UTC)})

        # check in cases
        if value in self.cases:
            return self.cases[value]
        elif "else" in self.cases:
            return self.cases["else"]
        else:
            raise ValueError("Invalid choice")

    async def can_run(self, data: TaskData | None) -> bool:
        script = self.__get_script()
        can_run = await script.can_run(data)
        self._cant_run_reason = script.cant_run_reason()
        return can_run

    async def run(self, data: TaskData | None) -> None:
        script = self.__get_script()
        await script.run(data)

    def get_fits_headers(self, namespaces: list[str] | None = None) -> dict[str, Any]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        script = self.__get_script()
        return script.get_fits_headers(namespaces)

    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        """Estimate duration of the script for the current case."""
        script = self.__get_script()
        return script.estimate_duration(data, time)


__all__ = ["CasesRunner"]
