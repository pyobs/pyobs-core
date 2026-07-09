from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pyobs.interfaces import FitsHeaderEntry
from pyobs.robotic.scripts import Script
from pyobs.robotic.storage.lco._portal import LcoRequest

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
    from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class LcoScript(Script):
    """Script for LCO configs.

    Dispatches to one of the named scripts in ``scripts``, selected via the
    configuration's ``extra_params["script_name"]``, as sent by the LCO portal.
    """

    request: LcoRequest
    scripts: dict[str, dict[str, Any]] = {}

    def _create_script(self) -> Script:
        """Build the script selected via the configuration's extra_params["script_name"].

        Raises:
            ValueError: If no script_name is given, or no matching script is configured.
        """
        script_name = self.request.configurations[0].extra_params.get("script_name")
        if script_name is None:
            raise ValueError("No script_name given in configuration's extra_params.")
        if script_name not in self.scripts:
            raise ValueError(f'No script found for script_name "{script_name}".')
        return self.pyobs_model_validate(Script, self.scripts[script_name], by_alias=True)

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this config can currently run.

        Returns:
            True, if the script can run now
        """
        script = self._create_script()
        can_run = await script.can_run(data)
        self._cant_run_reason = script.cant_run_reason()
        return can_run

    async def run(self, data: TaskData | None) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """
        script = self._create_script()
        try:
            await script.run(data)
        finally:
            self.exptime_done = script.exptime_done

    def get_fits_headers(self, namespaces: list[str] | None = None) -> dict[str, FitsHeaderEntry]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        return self._create_script().get_fits_headers(namespaces)

    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        """Estimate duration based on the duration calculated by the LCO portal."""
        return float(self.request.duration)


__all__ = ["LcoScript"]
