from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from pyobs.interfaces import IPointingAltAz, IReady
from pyobs.robotic.scripts import Script
from pyobs.robotic.utils.skyflats.pointing import SkyFlatsBasePointing

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
    from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class PointingScript(Script):
    """Script for pointing the telescope for flats."""

    telescope: Annotated[str, IPointingAltAz, IReady] = Field(description="Name of the telescope module to point.")
    pointing: SkyFlatsBasePointing = Field(description="Strategy used to compute the flat-field pointing.")

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """
        if not await self.comm.has_proxy(self.telescope, IPointingAltAz):
            self._cant_run_reason = "No telescope found."
            return False

        async with self.comm.proxy(self.telescope, IReady) as telescope:
            ready_state = telescope.get_state(IReady)
            if ready_state is None or not ready_state.ready:
                self._cant_run_reason = "Telescope not ready."
                return False

        self._cant_run_reason = None
        return True

    async def run(self, data: TaskData | None) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """
        async with self.comm.proxy(self.telescope, IPointingAltAz) as telescope:
            await self.pointing(telescope)
            log.info("Finished pointing telescope.")

    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        """Estimate duration of slewing to the flat-field pointing."""
        capabilities = data.instrument_capabilities if data is not None else None
        telescope = capabilities.telescope(self.telescope) if capabilities is not None else None
        slew_time = telescope.estimate_slew_time_s() if telescope is not None else None
        return slew_time if slew_time is not None else 60.0


__all__ = ["PointingScript"]
