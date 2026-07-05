from __future__ import annotations

import asyncio
import logging
import math
import random
from typing import Any

from pyobs.interfaces import AcquisitionAttempt, AcquisitionResult, AcquisitionState, IAcquisition, IRunning
from pyobs.interfaces.IRunning import RunningState
from pyobs.modules import Module, timeout
from pyobs.utils import exceptions as exc
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class DummyAcquisition(Module, IAcquisition):
    """Dummy class for telescope acquisition."""

    __module__ = "pyobs.modules.acquisition"

    def __init__(
        self,
        wait_secs: float = 1.0,
        start_distance: float = 60.0,
        tolerance: float = 1.0,
        max_attempts: int = 5,
        **kwargs: Any,
    ):
        """Create a new dummy acquisition.

        Args:
            wait_secs: Time to wait between attempts, in seconds.
            start_distance: Simulated initial distance to target, in arcsec.
            tolerance: Distance within which the target counts as acquired, in arcsec.
            max_attempts: Number of attempts before giving up.
        """
        Module.__init__(self, **kwargs)

        # store
        self._wait_secs = wait_secs
        self._start_distance = start_distance
        self._tolerance = tolerance
        self._max_attempts = max_attempts
        self._is_running = False
        self._abort = asyncio.Event()

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)
        await self.comm.set_state(IAcquisition, AcquisitionState())
        await self.comm.set_state(IRunning, RunningState(running=False))

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        return self._is_running

    @timeout(120)
    async def acquire_target(self, **kwargs: Any) -> AcquisitionResult:
        """Acquire target at given coordinates.

        If no RA/Dec are given, start from current position. Might not work for some implementations that require
        coordinates.

        Returns:
            Result with time, ra, dec, alt, az, and either off_ra/off_dec or off_alt/off_az offsets.

        Raises:
            ValueError: If target could not be acquired.
        """

        try:
            self._is_running = True
            self._abort = asyncio.Event()
            await self.comm.set_state(IRunning, RunningState(running=True))
            return await self._acquire()
        finally:
            self._is_running = False
            await self.comm.set_state(IRunning, RunningState(running=False))

    async def _acquire(self) -> AcquisitionResult:
        """Actually acquire target."""
        attempts: list[AcquisitionAttempt] = []
        await self.comm.set_state(IAcquisition, AcquisitionState(attempts=attempts))

        distance = self._start_distance
        bearing = random.uniform(0.0, 2 * math.pi)  # direction of the offset, wanders a bit each attempt
        for a in range(1, self._max_attempts + 1):
            if self._abort.is_set():
                raise exc.AbortedError()

            acquired = distance < self._tolerance
            offset_deg = distance / 3600.0
            offset_ra = offset_deg * math.cos(bearing)
            offset_dec = offset_deg * math.sin(bearing)
            log.info("Attempt %d: distance to target %.2f arcsec.", a, distance)
            attempts = attempts + [
                AcquisitionAttempt(
                    attempt=a,
                    distance=distance,
                    offset_applied=not acquired,
                    offset_ra=offset_ra,
                    offset_dec=offset_dec,
                )
            ]
            await self.comm.set_state(IAcquisition, AcquisitionState(attempts=attempts))

            await asyncio.sleep(self._wait_secs)

            if acquired:
                log.info("Target successfully acquired.")
                result = AcquisitionResult(
                    time=Time.now(), ra=0.0, dec=0.0, alt=0.0, az=0.0, off_ra=offset_ra, off_dec=offset_dec
                )
                await self.comm.set_state(IAcquisition, AcquisitionState(attempts=attempts, result=result))
                return result

            # converge towards the tolerance, with a bit of noise, and let the bearing wander a little
            distance = max(self._tolerance * 0.5, distance / 3 + random.gauss(0.0, distance * 0.05))
            bearing += random.gauss(0.0, 0.4)

        raise exc.AcquisitionError("Could not acquire target within given tolerance.")

    async def abort(self, **kwargs: Any) -> None:
        self._abort.set()


__all__ = ["DummyAcquisition"]
