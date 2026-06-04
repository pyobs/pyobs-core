from __future__ import annotations
from datetime import datetime, UTC
import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
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
        return await script.can_run(data)

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


__all__ = ["CasesRunner"]
