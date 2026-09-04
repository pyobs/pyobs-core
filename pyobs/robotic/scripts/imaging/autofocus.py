from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from pyobs.interfaces import IAutoFocus, IDome, IMotion, IPointingRaDec, IReady, ITelescope
from pyobs.robotic.scripts import Script
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData

log = logging.getLogger(__name__)


class AutoFocusScript(Script):
    """Script for running autofocus series."""

    autofocus: Annotated[str, IAutoFocus] = Field(
        default="autofocus", description="Name of the auto-focus module to run the series with."
    )
    telescope: Annotated[str, ITelescope, IPointingRaDec] = Field(
        default="telescope", description="Name of the telescope module, moved to the target and stopped afterwards."
    )
    dome: Annotated[str | None, IDome] = Field(
        default=None, description="Name of the dome module, if the site has a rotating dome (omit for a plain roof)."
    )
    count: int = Field(default=5, description="Number of focus steps to take in the series.")
    step: float = Field(default=0.1, description="Focus step size.")
    exposure_time: float = Field(default=2.0, description="Exposure time in seconds for each focus step.")

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this config can currently run.
        Returns:
            True if script can run now.
        """

        # we need a target to focus on
        if data is None or data.task is None or data.resolved_target is None:
            self._cant_run_reason = "No target given."
            return False

        # we need a camera
        if not await self.comm.has_proxy(self.autofocus, IAutoFocus):
            self._cant_run_reason = "No autofocus found."
            return False

        # ready?
        async with self.comm.safe_proxy(self.telescope, ITelescope) as telescope:
            if telescope is None:
                self._cant_run_reason = "No ITelescope found."
                return False
            ready_state = telescope.get_state(IReady)
            if ready_state is None or not ready_state.ready:
                self._cant_run_reason = "Telescope not ready."
                return False

        # all good
        self._cant_run_reason = None
        return True

    async def run(self, data: TaskData | None) -> None:
        """Run script.
        Raises:
            InterruptedError: If interrupted
        """
        if data is None or data.task is None:
            return

        target = data.resolved_target
        if target is None:
            raise ValueError("No target given.")
        log.info("Picked target %s for auto focus...", target)

        log.info("Moving telescope...")
        coord = target.coordinates(Time.now())
        async with self.comm.proxy(self.telescope, IPointingRaDec) as telescope:
            await telescope.move_radec(coord.ra.degree, coord.dec.degree)

        try:
            log.info("Performing auto focus...")
            async with self.comm.proxy(self.autofocus, IAutoFocus) as autofocus:
                await autofocus.auto_focus(self.count, self.step, self.exposure_time)

        finally:
            async with self.comm.safe_proxy(self.telescope, IMotion) as telescope:
                if telescope is not None:
                    log.info("Stopping telescope...")
                    await telescope.stop_motion()
            log.info("Done.")

    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        """Estimate duration of the autofocus run.

        Telescope and dome move in parallel, so time-to-ready is the slower of the two, not their
        sum -- falls back to the flat 60.0 fudge only when neither yields a real estimate.
        """
        capabilities = data.instrument_capabilities if data is not None else None
        telescope = capabilities.telescope(self.telescope) if capabilities is not None else None
        slew_time = telescope.estimate_slew_time_s() if telescope is not None else None
        dome = capabilities.dome(self.dome) if capabilities is not None and self.dome else None
        rotate_time = dome.estimate_rotate_time_s() if dome is not None else None

        times = [t for t in (slew_time, rotate_time) if t is not None]
        return self.count * self.exposure_time + (max(times) if times else 60.0)


__all__ = ["AutoFocusScript"]
