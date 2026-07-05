import asyncio
import logging
import math
import random
from typing import Any

from pyobs.events import FocusFoundEvent
from pyobs.interfaces import IAutoFocus, IRunning
from pyobs.interfaces.IAutoFocus import AutoFocusPoint, AutoFocusResult, AutoFocusState
from pyobs.interfaces.IRunning import RunningState
from pyobs.modules import Module
from pyobs.utils import exceptions as exc

log = logging.getLogger(__name__)


class DummyAutoFocus(Module, IAutoFocus):
    """Dummy class for auto-focusing a telescope."""

    __module__ = "pyobs.modules.focus"

    def __init__(
        self,
        wait_time: float = 0.5,
        best_focus: float = 10.0,
        min_value: float = 3.0,
        curve_width: float = 0.076,
        **kwargs: Any,
    ):
        """Create a new dummy auto-focus.

        Args:
            wait_time: Time to wait between focus steps, in seconds.
            best_focus: Focus value the series converges to.
            min_value: Value (e.g. HFD) at the focus curve's minimum.
            curve_width: Width parameter of the focus curve; with the defaults, a
                count=5/step=0.1 series (the typical case) spans from min_value at the
                centre to about 20 at the outer points.
        """
        Module.__init__(self, **kwargs)

        self._wait_time = wait_time
        self._best_focus = best_focus
        self._min_value = min_value
        self._curve_width = curve_width
        self._running = False
        self._abort = asyncio.Event()

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)
        await self.comm.register_event(FocusFoundEvent)
        await self.comm.set_state(IAutoFocus, AutoFocusState())
        await self.comm.set_state(IRunning, RunningState(running=False))

    async def auto_focus(self, count: int, step: float, exposure_time: float, **kwargs: Any) -> AutoFocusResult:
        """Perform an autofocus series.

        Args:
            count: Number of images to take on each side of the initial guess.
            step: Step size.
            exposure_time: Exposure time for images.

        Returns:
            Result of autofocus.

        Raises:
            ValueError: If focus could not be obtained.
        """

        try:
            self._running = True
            self._abort = asyncio.Event()
            await self.comm.set_state(IRunning, RunningState(running=True))
            return await self._auto_focus(count, step)
        finally:
            self._running = False
            await self.comm.set_state(IRunning, RunningState(running=False))

    async def _auto_focus(self, count: int, step: float) -> AutoFocusResult:
        # a real focus curve (HFD/FWHM vs. focus position) is a hyperbola, not a parabola:
        # value(x) = sqrt(min_value^2 + ((x - best_focus) / curve_width)^2)
        points: list[AutoFocusPoint] = []
        await self.comm.set_state(IAutoFocus, AutoFocusState(points=points))

        for i in range(-count, count + 1):
            if self._abort.is_set():
                raise exc.AbortedError()

            focus = self._best_focus + i * step
            value = math.sqrt(self._min_value**2 + ((focus - self._best_focus) / self._curve_width) ** 2)
            value += random.gauss(0.0, self._min_value * 0.05)
            points = points + [AutoFocusPoint(focus=focus, value=value)]
            await self.comm.set_state(IAutoFocus, AutoFocusState(points=points))

            await asyncio.sleep(self._wait_time)

        error = abs(random.gauss(0.0, step / 10))
        await self.comm.send_event(FocusFoundEvent(self._best_focus, error))
        return AutoFocusResult(focus=self._best_focus, focus_err=error)

    async def is_running(self, **kwargs: Any) -> bool:
        """Whether a service is running."""
        return self._running

    async def abort(self, **kwargs: Any) -> None:
        """Abort current actions."""
        self._abort.set()


__all__ = ["DummyAutoFocus"]
