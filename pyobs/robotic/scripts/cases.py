from __future__ import annotations
from datetime import datetime, timezone
import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class CasesRunner(Script):
    """Script for distinguishing cases."""

    expression: str
    cases: dict[str | int | float, Any]

    def __get_script(self) -> Script:
        # evaluate condition
        value = eval(self.expression, {"now": datetime.now(timezone.utc), "config": self.configuration})

        # check in cases
        if value in self.cases:
            return Script.model_validate(self.cases[value])
        elif "else" in self.cases:
            return Script.model_validate(self.cases["else"])
        else:
            raise ValueError("Invalid choice")

    async def can_run(self, data: TaskData) -> bool:
        script = self.__get_script()
        return await script.can_run(data)

    async def run(self, data: TaskData) -> None:
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
