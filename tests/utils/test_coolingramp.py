from __future__ import annotations

import pytest

from pyobs.utils.coolingramp import CoolingRamp


def run(ramp: CoolingRamp, commanded: float, enabled: bool, target: float | None, tracking: float | None = None):
    """Runs the planner to the end, returns list of (enabled, setpoint, delay) writes.

    tracking: if given, the sensor follows the setpoint at that offset (sensor = setpoint - tracking).
    """
    writes = []
    for _ in range(1000):
        sensor = None if tracking is None else commanded - tracking
        step = ramp.next_step(commanded, enabled, target, sensor)
        if step.write:
            writes.append((step.enabled, step.setpoint, step.delay))
            if step.setpoint is not None:
                commanded = step.setpoint
        if step.done:
            return writes
    raise AssertionError("ramp did not finish")


def test_cool_down_steps_and_delay() -> None:
    ramp = CoolingRamp(rate_warm=1.0, rate_cool=2.0, step=1.0)
    writes = run(ramp, 20.0, True, 17.0)
    assert [w[1] for w in writes] == [19.0, 18.0, 17.0]
    assert writes[0][2] == pytest.approx(30.0)  # 1 degC at 2 degC/min
    assert writes[-1][2] == 0.0


def test_warm_up_uses_warm_rate() -> None:
    ramp = CoolingRamp(rate_warm=1.0, rate_cool=2.0, step=1.0)
    writes = run(ramp, -20.0, True, -18.0)
    assert [w[1] for w in writes] == [-19.0, -18.0]
    assert writes[0][2] == pytest.approx(60.0)


def test_none_rate_is_one_step() -> None:
    ramp = CoolingRamp(rate_warm=1.0, rate_cool=None)
    assert [w[1] for w in run(ramp, 20.0, True, -20.0)] == [-20.0]


def test_target_equals_commanded_writes_nothing() -> None:
    step = CoolingRamp().next_step(-10.0, True, -10.0, None)
    assert step.done and not step.write


def test_last_step_is_smaller_than_step() -> None:
    ramp = CoolingRamp(rate_warm=1.0, rate_cool=1.0, step=2.0)
    assert [w[1] for w in run(ramp, 0.0, True, -3.0)] == [-2.0, -3.0]


def test_resolution_rounds_and_widens_step() -> None:
    ramp = CoolingRamp(rate_warm=1.0, rate_cool=1.0, step=0.5, resolution=1.0)
    assert ramp.step == 1.0
    assert [w[1] for w in run(ramp, 0.0, True, -2.4)] == [-1.0, -2.0]


def test_disable_ramps_to_off_temperature_then_switches_off() -> None:
    ramp = CoolingRamp(rate_warm=1.0, off_temperature=-17.0)
    writes = run(ramp, -20.0, False, None, tracking=0.5)
    assert [(w[0], w[1]) for w in writes] == [(True, -19.0), (True, -18.0), (True, -17.0), (False, None)]


def test_disable_stops_early_when_sensor_stops_following() -> None:
    # ambient 5 degC: setpoint passes sensor + 1 on the way, cooler is idle, so switch off
    ramp = CoolingRamp(rate_warm=1.0, off_temperature=20.0)
    step = ramp.next_step(6.0, False, None, sensor=5.0)
    assert step.done and step.enabled is False and step.setpoint is None


def test_disable_without_warm_rate_switches_off_at_once() -> None:
    step = CoolingRamp(rate_warm=None, rate_cool=2.0).next_step(-20.0, False, None, sensor=-20.0)
    assert step.done and step.enabled is False


def test_enable_requires_setpoint() -> None:
    with pytest.raises(ValueError):
        CoolingRamp().next_step(0.0, True, None, None)


@pytest.mark.parametrize("kwargs", [{"step": 0.0}, {"rate_warm": 0.0}, {"rate_cool": -1.0}])
def test_invalid_config(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        CoolingRamp(**kwargs)
