from __future__ import annotations

import asyncio
import logging
from typing import Any

from pyobs.interfaces import CoolingState
from pyobs.utils.coolingramp import CoolingRamp

log = logging.getLogger(__name__)

_MAX_QUIET_FAILURES = 5
_RETRY_DELAY = 5.0


class CoolingRampMixin:
    """Mixin for ICooling modules that moves the cooling setpoint in steps instead of one jump.

    The mixin implements ``ICooling.set_cooling``. A new target is stored and a background loop moves
    the commanded setpoint towards it, using ``pyobs.utils.coolingramp.CoolingRamp`` for the steps.

    Drivers implement three hooks:

    * ``_set_cooling_hardware(enabled, setpoint)``: one immediate write to the camera.
    * ``_get_cooling_hardware()``: ``(enabled, setpoint or None, power or None)`` read from the camera.
    * ``_get_sensor_temperature()``: current sensor temperature, or ``None``.

    Put this mixin before the camera base class in the bases, so that its ``set_cooling`` is used.
    """

    __module__ = "pyobs.mixins"

    # Resolution of the camera's setpoint in degC, if limited (e.g. 1.0 for integer setpoints).
    _cooling_setpoint_resolution: float | None = None

    def __init__(
        self,
        cooling_rate_warm: float | None = 1.0,
        cooling_rate_cool: float | None = 2.0,
        cooling_ramp_step: float = 1.0,
        cooling_off_temperature: float = 20.0,
        cooling_warmup_on_close: bool = False,
        cooling_close_timeout: float = 60.0,
        **kwargs: Any,
    ):
        """Creates the mixin.

        Args:
            cooling_rate_warm: Maximum rate in degC/min when raising the setpoint or switching cooling off.
                None for a single step.
            cooling_rate_cool: Maximum rate in degC/min when lowering the setpoint. None for a single step.
            cooling_ramp_step: Setpoint change per hardware write in degC. The interval follows from the rate.
            cooling_off_temperature: Temperature the setpoint is ramped to before cooling is switched off.
            cooling_warmup_on_close: Warm up to cooling_off_temperature and switch cooling off when closing.
            cooling_close_timeout: Maximum time in seconds that warm-up on close may take.
        """
        super().__init__(**kwargs)

        self._cooling_ramp = CoolingRamp(
            rate_warm=cooling_rate_warm,
            rate_cool=cooling_rate_cool,
            step=cooling_ramp_step,
            off_temperature=cooling_off_temperature,
            resolution=self._cooling_setpoint_resolution,
        )
        self._cooling_warmup_on_close = cooling_warmup_on_close
        self._cooling_close_timeout = cooling_close_timeout

        # (enabled, setpoint) requested last, while a ramp towards it is running
        self._cooling_target: tuple[bool, float | None] | None = None
        # last setpoint written to the hardware by this mixin
        self._cooling_commanded: float | None = None
        self._cooling_event = asyncio.Event()
        self._cooling_failures = 0

        self._cooling_task = self.add_background_task(self._cooling_ramp_loop, True)  # type: ignore[attr-defined]

    # hooks ------------------------------------------------------------------------------------------------------

    async def _set_cooling_hardware(self, enabled: bool, setpoint: float | None) -> None:
        raise NotImplementedError

    async def _get_cooling_hardware(self) -> tuple[bool, float | None, int | None]:
        raise NotImplementedError

    async def _get_sensor_temperature(self) -> float | None:
        raise NotImplementedError

    # public -----------------------------------------------------------------------------------------------------

    @property
    def cooling_ramping(self) -> bool:
        """Whether a ramp towards a cooling target is in progress."""
        return self._cooling_target is not None

    def _cooling_state(self, power: int | None, enabled: bool, setpoint: float | None) -> CoolingState:
        """Builds a CoolingState from hardware values, adding the ramp target and flag."""
        target = self._cooling_target
        goal = self._cooling_ramp.goal(*target) if target is not None else None
        return CoolingState(setpoint=setpoint, power=power, enabled=enabled, target=goal, ramping=target is not None)

    async def set_cooling(self, enabled: bool, setpoint: float, **kwargs: Any) -> None:
        """Enables/disables cooling and sets setpoint.

        Returns at once if a ramp is needed, the ramp then runs in the background.

        Args:
            enabled: Enable or disable cooling.
            setpoint: Setpoint in celsius for the cooling.
            ramp: Optional keyword. If False, the change is written in one step.

        Raises:
            ValueError: If cooling could not be set (only for immediate changes).
        """
        immediate = not kwargs.get("ramp", True) or self._cooling_ramp.immediate
        if enabled:
            log.info("Enabling cooling with a setpoint of %.2f°C%s.", setpoint, "" if immediate else " (ramping)")
        else:
            log.info("Disabling cooling%s.", "" if immediate else " (ramping up first)")

        if immediate:
            self._cooling_target = None
            value = self._cooling_ramp.round(setpoint) if enabled else None
            await self._set_cooling_hardware(enabled, value)
            self._cooling_commanded = value
            return

        self._cooling_target = (enabled, setpoint if enabled else None)
        self._cooling_event.set()

    async def close(self) -> None:
        """Stops the ramp. Optionally warms up and switches cooling off first, within a time limit."""
        self._cooling_task.stop()
        if self._cooling_warmup_on_close:
            self._cooling_target = (False, None)
            try:
                await asyncio.wait_for(self._cooling_run_to_end(), self._cooling_close_timeout)
            except TimeoutError:
                log.warning(
                    "Warm-up on close did not finish within %.0fs, leaving setpoint at %s.",
                    self._cooling_close_timeout,
                    self._cooling_commanded,
                )
        elif self._cooling_target is not None:
            log.info(
                "Closing with cooling setpoint at %s (target %s), leaving cooler as it is.",
                self._cooling_commanded,
                self._cooling_target,
            )
        await super().close()  # type: ignore[misc]

    # ramp -------------------------------------------------------------------------------------------------------

    async def _cooling_run_to_end(self) -> None:
        while self._cooling_target is not None:
            delay = await self._cooling_tick()
            if delay:
                await asyncio.sleep(delay)

    async def _cooling_ramp_loop(self) -> None:
        while True:
            if self._cooling_target is None:
                await self._cooling_event.wait()
                self._cooling_event.clear()
                continue

            try:
                delay = await self._cooling_tick()
                self._cooling_failures = 0
            except Exception as e:
                self._cooling_failures += 1
                if self._cooling_failures == _MAX_QUIET_FAILURES:
                    log.error("Cooling ramp failed %d times in a row, still retrying: %s", self._cooling_failures, e)
                else:
                    log.warning("Cooling ramp step failed: %s", e)
                delay = _RETRY_DELAY

            if not delay:
                continue
            try:
                await asyncio.wait_for(self._cooling_event.wait(), delay)
                self._cooling_event.clear()
            except TimeoutError:
                pass

    async def _cooling_tick(self) -> float | None:
        """Performs one ramp step towards the current target.

        Returns:
            Seconds until the next step, or None if the target was reached (or there is none).
        """
        target = self._cooling_target
        if target is None:
            return None
        enabled, setpoint = target

        # find a start point if we do not know what we last wrote
        if self._cooling_commanded is None:
            hw_enabled, hw_setpoint, _ = await self._get_cooling_hardware()
            if hw_enabled and hw_setpoint is not None:
                self._cooling_commanded = hw_setpoint
            elif not enabled:
                # already off, nothing to warm up
                self._finish(target)
                return None
            else:
                sensor = await self._get_sensor_temperature()
                start = self._cooling_ramp.round(sensor if sensor is not None else self._cooling_ramp.goal(*target))
                await self._set_cooling_hardware(True, start)
                self._cooling_commanded = start

        commanded = self._cooling_commanded
        assert commanded is not None
        sensor = None if enabled else await self._get_sensor_temperature()
        step = self._cooling_ramp.next_step(commanded, enabled, setpoint, sensor)
        if step.write:
            await self._set_cooling_hardware(step.enabled, step.setpoint)
            self._cooling_commanded = step.setpoint
        if step.done:
            self._finish(target)
            return None
        return step.delay

    def _finish(self, target: tuple[bool, float | None]) -> None:
        """Marks target as done unless a newer one was set in the meantime."""
        if self._cooling_target is target:
            self._cooling_target = None


__all__ = ["CoolingRampMixin"]
