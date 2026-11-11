"""Tests for CoolingRampMixin, using DummyCamera as the adopting module. Ticks are driven directly so that
no timing is involved."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pyobs.modules.camera.dummycamera import CoolingStatus, DummyCamera


def make_camera(**kwargs: float | None) -> DummyCamera:
    camera = DummyCamera(readout_time=0, **kwargs)  # type: ignore[arg-type]
    camera.comm.set_state = AsyncMock()
    return camera


def track_setpoint(camera: DummyCamera, offset: float = 0.5) -> None:
    """Makes the simulated sensor follow the setpoint, like a camera that is still cooling."""
    camera._get_sensor_temperature = AsyncMock(  # type: ignore[method-assign]
        side_effect=lambda: camera._cooling.set_point - offset
    )


async def run_ticks(camera: DummyCamera) -> list[float | None]:
    """Runs ticks until the ramp is done, returns the setpoints seen after each tick."""
    seen = []
    for _ in range(1000):
        if not camera.cooling_ramping:
            return seen
        await camera._cooling_tick()
        seen.append(camera._cooling.set_point if camera._cooling.enabled else None)
    raise AssertionError("ramp did not finish")


@pytest.mark.asyncio
async def test_default_dummy_changes_in_one_step() -> None:
    camera = make_camera()
    await camera.set_cooling(True, -30.0)
    assert camera._cooling.set_point == -30.0
    assert not camera.cooling_ramping


@pytest.mark.asyncio
async def test_set_cooling_returns_before_target_reached() -> None:
    camera = make_camera(cooling_rate_cool=2.0, cooling_rate_warm=1.0)
    await camera.set_cooling(True, -30.0)
    assert camera.cooling_ramping
    assert camera._cooling.set_point == CoolingStatus().set_point  # untouched until the loop runs


@pytest.mark.asyncio
async def test_cool_down_starts_at_hardware_setpoint() -> None:
    camera = make_camera(cooling_rate_cool=2.0, cooling_rate_warm=1.0)
    await camera.set_cooling(True, -13.0)  # hardware is at -10
    assert await run_ticks(camera) == [-11.0, -12.0, -13.0]


@pytest.mark.asyncio
async def test_retarget_continues_from_commanded_value() -> None:
    camera = make_camera(cooling_rate_cool=2.0, cooling_rate_warm=1.0)
    await camera.set_cooling(True, -14.0)
    await camera._cooling_tick()
    await camera._cooling_tick()
    assert camera._cooling.set_point == -12.0

    await camera.set_cooling(True, -11.0)  # reverse, no jump
    assert await run_ticks(camera) == [-11.0]


@pytest.mark.asyncio
async def test_disable_ramps_up_then_switches_off() -> None:
    camera = make_camera(cooling_rate_cool=2.0, cooling_rate_warm=1.0, cooling_off_temperature=-7.0)
    track_setpoint(camera)
    await camera.set_cooling(False, 0.0)
    assert await run_ticks(camera) == [-9.0, -8.0, -7.0, None]
    assert camera._cooling.enabled is False


@pytest.mark.asyncio
async def test_disable_stops_early_when_sensor_stops_following() -> None:
    camera = make_camera(cooling_rate_cool=2.0, cooling_rate_warm=1.0)
    camera._cooling = camera._cooling._replace(temperatures={"CCD": -8.0, "Back": 3.0})  # setpoint -10
    await camera.set_cooling(False, 0.0)
    # sensor stays at -8, so the cooler is idle once the setpoint reaches -7 (sensor + 1)
    assert await run_ticks(camera) == [-9.0, -8.0, -7.0, None]


@pytest.mark.asyncio
async def test_unknown_start_uses_sensor_when_cooler_is_off() -> None:
    camera = make_camera(cooling_rate_cool=2.0, cooling_rate_warm=1.0)
    camera._cooling = camera._cooling._replace(enabled=False, temperatures={"CCD": 5.0, "Back": 3.0})
    await camera.set_cooling(True, 3.0)
    assert await run_ticks(camera) == [4.0, 3.0]  # first write enables at the sensor temperature, 5.0


@pytest.mark.asyncio
async def test_ramp_false_writes_immediately() -> None:
    camera = make_camera(cooling_rate_cool=2.0, cooling_rate_warm=1.0)
    await camera.set_cooling(True, -30.0, ramp=False)
    assert camera._cooling.set_point == -30.0
    assert not camera.cooling_ramping


@pytest.mark.asyncio
async def test_new_target_replaces_running_one() -> None:
    camera = make_camera(cooling_rate_cool=2.0, cooling_rate_warm=1.0)
    await camera.set_cooling(True, -20.0)
    await camera.set_cooling(True, -12.0)
    assert await run_ticks(camera) == [-11.0, -12.0]


@pytest.mark.asyncio
async def test_state_reports_target_and_ramping() -> None:
    camera = make_camera(cooling_rate_cool=2.0, cooling_rate_warm=1.0)
    await camera.set_cooling(True, -20.0)
    state = camera._cooling_state(50, True, -10.0)
    assert state.ramping is True and state.target == -20.0 and state.setpoint == -10.0

    await camera.set_cooling(False, 0.0)
    assert camera._cooling_state(50, True, -10.0).target == 20.0

    await camera.set_cooling(True, -10.0, ramp=False)
    state = camera._cooling_state(50, True, -10.0)
    assert state.ramping is False and state.target is None


@pytest.mark.asyncio
async def test_tick_error_propagates_to_loop_and_keeps_target() -> None:
    camera = make_camera(cooling_rate_cool=2.0, cooling_rate_warm=1.0)
    await camera.set_cooling(True, -20.0)
    camera._set_cooling_hardware = AsyncMock(side_effect=OSError("boom"))  # type: ignore[method-assign]
    with pytest.raises(OSError):
        await camera._cooling_tick()
    assert camera.cooling_ramping


@pytest.mark.asyncio
async def test_close_without_warmup_leaves_setpoint() -> None:
    camera = make_camera(cooling_rate_cool=2.0, cooling_rate_warm=1.0)
    await camera.set_cooling(True, -20.0, ramp=False)
    await camera.close()
    assert camera._cooling.enabled is True
    assert camera._cooling.set_point == -20.0


@pytest.mark.asyncio
async def test_close_with_warmup_switches_off_within_timeout() -> None:
    camera = make_camera(
        cooling_rate_cool=2.0,
        cooling_rate_warm=600.0,  # 1 degC every 0.1 s
        cooling_warmup_on_close=True,
        cooling_close_timeout=30.0,
        cooling_off_temperature=-8.0,
    )
    track_setpoint(camera)
    await camera.close()
    assert camera._cooling.enabled is False


@pytest.mark.asyncio
async def test_close_with_warmup_times_out() -> None:
    camera = make_camera(
        cooling_rate_cool=2.0,
        cooling_rate_warm=0.5,
        cooling_warmup_on_close=True,
        cooling_close_timeout=0.2,
        cooling_off_temperature=20.0,
    )
    track_setpoint(camera)
    await camera.close()
    assert camera._cooling.enabled is True  # not finished, cooler left on at an intermediate setpoint
