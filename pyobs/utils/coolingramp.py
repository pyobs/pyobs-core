from __future__ import annotations

import math
from dataclasses import dataclass

# While the setpoint is at least this much above the sensor temperature, the cooler is idle and the
# sensor no longer follows the setpoint, so a warm-up can stop and the cooler be switched off.
IDLE_MARGIN = 1.0

# A camera without a real off switch is "switched off" by writing a setpoint above the sensor temperature. This is
# how far above the off temperature that setpoint may go, so that a sensor at a much higher temperature than
# expected cannot lead to a setpoint the camera rejects.
MAX_OFF_ABOVE = 10.0


@dataclass(frozen=True)
class RampStep:
    """What to do next in a cooling ramp.

    Attributes:
        write: Whether to write ``enabled``/``setpoint`` to the hardware.
        enabled: Cooler state to write.
        setpoint: Setpoint to write, None if the cooler is to be switched off.
        done: Whether the ramp has reached its target after this step.
        delay: Seconds to wait before asking for the next step (0 if done).
    """

    write: bool
    enabled: bool
    setpoint: float | None
    done: bool
    delay: float


class CoolingRamp:
    """Plans the steps of a cooling setpoint ramp. No I/O, no timing: callers write the steps and wait.

    Shared by the ``CoolingRampMixin`` for modules and by local GUIs that talk to a camera SDK directly.
    Warming up (raising the setpoint or switching the cooler off) has its own rate, since that is the
    direction that can damage a sensor or cause condensation.
    """

    def __init__(
        self,
        rate_warm: float | None = 1.0,
        rate_cool: float | None = 2.0,
        step: float = 1.0,
        off_temperature: float = 20.0,
        resolution: float | None = None,
    ):
        """Creates a new planner.

        Args:
            rate_warm: Maximum rate in degC/min when raising the setpoint or switching off. None for one step.
            rate_cool: Maximum rate in degC/min when lowering the setpoint. None for one step.
            step: Setpoint change per write in degC. The delay between writes follows from the rate.
            off_temperature: Temperature the setpoint is ramped to before the cooler is switched off.
            resolution: Resolution of the camera's setpoint in degC (e.g. 1.0 for integer setpoints).
        """
        if step <= 0:
            raise ValueError("step must be positive.")
        for rate in (rate_warm, rate_cool):
            if rate is not None and rate <= 0:
                raise ValueError("Rates must be positive or None.")
        self.rate_warm = rate_warm
        self.rate_cool = rate_cool
        self.step = max(step, resolution or 0.0)
        self.off_temperature = off_temperature
        self.resolution = resolution

    @property
    def immediate(self) -> bool:
        """Whether every change is a single step, so no ramp is ever needed."""
        return self.rate_warm is None and self.rate_cool is None

    def round(self, value: float) -> float:
        """Rounds a setpoint to the camera's resolution."""
        return round(value / self.resolution) * self.resolution if self.resolution else value

    def goal(self, enabled: bool, target: float | None) -> float:
        """The temperature a ramp towards the given target ends at."""
        if enabled:
            if target is None:
                raise ValueError("A setpoint is required when enabling cooling.")
            return self.round(target)
        return self.off_temperature

    def off_setpoint(self, sensor: float | None) -> float:
        """Setpoint to write for "off" on a camera that has no real off switch.

        This is the off temperature, or, if the sensor is warmer than that (ambient above the off temperature), a
        setpoint just above the sensor temperature, so that the cooler stays idle instead of cooling below ambient.
        Raising the setpoint above the sensor does not heat the sensor, so this needs no ramp.

        Args:
            sensor: Current sensor temperature. May be None.

        Returns:
            The setpoint, rounded up to the camera's resolution.
        """
        if sensor is None or sensor + IDLE_MARGIN <= self.off_temperature:
            return self.off_temperature
        wanted = min(sensor + IDLE_MARGIN, self.off_temperature + MAX_OFF_ABOVE)
        if self.resolution:
            wanted = math.ceil(wanted / self.resolution) * self.resolution
        return wanted

    def next_step(self, commanded: float, enabled: bool, target: float | None, sensor: float | None) -> RampStep:
        """Plans the next step.

        Args:
            commanded: Setpoint currently set on the camera.
            enabled: Whether the target state is cooling on (True) or off (False).
            target: Target setpoint if enabled.
            sensor: Current sensor temperature, used to stop a warm-up early. May be None.

        Returns:
            The next step.
        """
        goal = self.goal(enabled, target)

        if not enabled:
            idle = sensor is not None and commanded >= sensor + IDLE_MARGIN
            if idle or commanded >= goal or self.rate_warm is None:
                return RampStep(write=True, enabled=False, setpoint=None, done=True, delay=0.0)
        elif commanded == goal:
            return RampStep(write=False, enabled=True, setpoint=commanded, done=True, delay=0.0)

        warming = goal > commanded
        rate = self.rate_warm if warming else self.rate_cool
        if rate is None or abs(goal - commanded) <= self.step:
            new = goal
        else:
            new = self.round(commanded + (self.step if warming else -self.step))

        # a reached warm-up end point still needs the switch-off, which the next step does
        done = enabled and new == goal
        delay = 0.0 if done else (60.0 * self.step / rate if rate is not None else 0.0)
        return RampStep(write=True, enabled=True, setpoint=new, done=done, delay=delay)


__all__ = ["CoolingRamp", "RampStep", "IDLE_MARGIN", "MAX_OFF_ABOVE"]
