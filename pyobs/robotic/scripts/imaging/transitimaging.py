from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from pydantic import PrivateAttr

from pyobs.robotic.scheduler.merits.transit import TransitMerit
from pyobs.robotic.scheduler.targets import Target
from pyobs.robotic.scripts.imaging.imaging import ImagingScript
from pyobs.utils.parallel import Future
from pyobs.utils.time import Time

if TYPE_CHECKING:
    from pyobs.robotic.task import TaskData

log = logging.getLogger(__name__)


class TransitImagingScript(ImagingScript):
    """Imaging script that runs until the end of a transit window.

    Requires a TransitMerit on the task. Overrides _run_configurations() to loop
    instrument configurations until transit_time + duration/2 + ingress.
    """

    _transit_merit: TransitMerit | None = PrivateAttr(default=None)

    async def can_run(self, data: TaskData | None) -> bool:
        """Whether this script can currently run.

        In addition to ImagingScript checks, requires a TransitMerit on the task.

        Returns:
            True if the script can run now.
        """
        if not await super().can_run(data):
            return False

        if data is None or data.task is None:
            self._cant_run_reason = "No task data."
            return False
        if not any(isinstance(m, TransitMerit) for m in data.task.merits):
            self._cant_run_reason = "No TransitMerit found on task."
            return False

        self._cant_run_reason = None
        return True

    @staticmethod
    def _get_transit_merit(data: TaskData | None) -> TransitMerit | None:
        """Returns the TransitMerit from the task, or None."""
        if data is None or data.task is None:
            return None
        for m in data.task.merits:
            if isinstance(m, TransitMerit):
                return m
        return None

    async def _run_configurations(self, target: Target | None, track: Future | asyncio.Task[Any]) -> None:
        """Loop instrument configurations until the transit window ends."""
        if self._transit_merit is None:
            raise ValueError("No TransitMerit found on task.")

        end_time: Time = self._transit_merit.end_time()
        log.info("Transit imaging will run until %s.", end_time.isot)

        repeat = 0
        while Time.now() < end_time:
            log.info("Starting transit repeat %d...", repeat + 1)
            await self._run_configuration(repeat % self.configuration.repeats, target, track)
            repeat += 1

        log.info("Transit window ended.")

    async def run(self, data: TaskData | None) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted.
            ValueError: If no TransitMerit found.
        """
        merit = self._get_transit_merit(data)
        if merit is None:
            raise ValueError("No TransitMerit found on task.")
        self._transit_merit = merit

        await super().run(data)

    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        """Estimate duration of the transit observation.

        Args:
            data: Task data containing the TransitMerit.
            time: If given, return remaining time until end of the *next* transit
                  window that starts at or after ``time``.
                  If None, return the full observable window (ingress + duration + ingress).

        Returns:
            Estimated duration in seconds.
        """
        merit = self._get_transit_merit(data)
        if merit is None:
            return super().estimate_duration(data, time)

        if time is None:
            # full observable window: ingress + duration + ingress
            return merit.duration * (1.0 + 2.0 * merit.ingress)
        else:
            import math

            # Find the next transit whose end_time is strictly after ``time``.
            # TransitMerit.periods_since_jd0() uses round(), which can return
            # a transit already in the past.  Use ceil() so we always get the
            # next future window.
            days = float(time.jd - merit.jd0)
            p = days / merit.period
            n = math.ceil(p)
            end_offset_days = (merit.duration / 2.0 + merit.ingress * merit.duration) / 86400.0
            end_jd = merit.jd0 + n * merit.period + end_offset_days
            return float(max(0.0, (end_jd - time.jd) * 86400.0))


__all__ = ["TransitImagingScript"]
