from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
from pyobs.robotic.scripts import Script

log = logging.getLogger(__name__)


class ConditionalRunner(Script):
    """Script for running an if condition."""

    condition: str
    true: dict[str, Any]
    false: dict[str, Any] | None = None

    def __get_script(self) -> Script | None:
        # evaluate condition
        ret = eval(self.condition, {"now": datetime.now(timezone.utc)})

        # run scripts
        if ret:
            return Script.model_validate(self.true)
        elif self.false is not None:
            return Script.model_validate(self.false)
        else:
            return None

    async def can_run(self, data: TaskData) -> bool:
        script = self.__get_script()
        return True if script is None else await script.can_run(data)

    async def run(self, data: TaskData) -> None:
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
