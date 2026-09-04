from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from pyobs.interfaces import IDome, IPointingAltAz, IReady, IRoof
from pyobs.robotic.scripts import Script
from pyobs.robotic.utils.skyflats.pointing import SkyFlatsBasePointing

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData
    from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class PointingScript(Script):
    """Script for pointing the telescope for flats."""

    telescope: Annotated[str, IPointingAltAz, IReady] = Field(description="Name of the telescope module to point.")
    dome: Annotated[str | None, IDome] = Field(
        default=None, description="Name of the dome module, if the site has a rotating dome (omit for a plain roof)."
    )
    roof: Annotated[str | None, IRoof] = Field(
        default=None, description="Name of the roof module, if the site has a plain open/close roof (omit for a dome)."
    )
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
        """Estimate duration of slewing to the flat-field pointing.

        Telescope and dome/roof move in parallel, so time-to-ready is the slowest of the three,
        not their sum -- falls back to the flat 60.0 fudge only when none yields a real estimate.
        """
        capabilities = data.instrument_capabilities if data is not None else None
        telescope = capabilities.telescope(self.telescope) if capabilities is not None else None
        slew_time = telescope.estimate_slew_time_s() if telescope is not None else None
        dome = capabilities.dome(self.dome) if capabilities is not None and self.dome else None
        rotate_time = dome.estimate_rotate_time_s() if dome is not None else None
        roof = capabilities.roof(self.roof) if capabilities is not None and self.roof else None
        roof_time = roof.open_close_time_s if roof is not None else None

        times = [t for t in (slew_time, rotate_time, roof_time) if t is not None]
        return max(times) if times else 60.0


__all__ = ["PointingScript"]
