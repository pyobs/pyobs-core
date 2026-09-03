from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.robotic.instruments import Instrument, InstrumentCapabilities, TelescopeCapability
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.robotic.scripts.imaging.autofocus import AutoFocusScript
from pyobs.robotic.task import TaskData
from tests.helpers import isinstance_class, make_proxy_cm


def make_script(**kwargs) -> AutoFocusScript:
    return AutoFocusScript.model_validate(kwargs, context={"comm": MagicMock()})


def make_task(target=None) -> TaskData:
    task = MagicMock()
    task.target = target
    return TaskData(task=task)


def make_telescope(ready=True, is_motion=True) -> MagicMock:
    from pyobs.interfaces import IMotion, IPointingRaDec, ITelescope
    from pyobs.interfaces.IReady import ReadyState

    interfaces = [IPointingRaDec, ITelescope]
    if is_motion:
        interfaces.append(IMotion)

    tel = MagicMock(spec=interfaces)
    tel.get_state = MagicMock(return_value=ReadyState(ready=ready))
    tel.move_radec = AsyncMock()
    tel.stop_motion = AsyncMock()
    tel.__class__ = isinstance_class("Telescope", interfaces)
    return tel


def make_autofocus() -> MagicMock:
    from pyobs.interfaces import IAutoFocus

    af = MagicMock(spec=[IAutoFocus])
    af.auto_focus = AsyncMock()
    return af


# ── can_run ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_can_run_true_when_ready() -> None:
    script = make_script()
    telescope = make_telescope(ready=True)
    script._comm.has_proxy = AsyncMock(return_value=True)
    script._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))
    target = SiderealTarget(name="Vega", ra=279.23, dec=38.78)
    assert await script.can_run(make_task(target=target)) is True


@pytest.mark.asyncio
async def test_can_run_false_when_no_data() -> None:
    script = make_script()
    assert await script.can_run(None) is False


@pytest.mark.asyncio
async def test_can_run_false_when_no_target() -> None:
    script = make_script()
    assert await script.can_run(make_task(target=None)) is False


@pytest.mark.asyncio
async def test_can_run_false_when_autofocus_unavailable() -> None:
    script = make_script()
    script._comm.has_proxy = AsyncMock(return_value=False)
    target = SiderealTarget(name="Vega", ra=279.23, dec=38.78)
    assert await script.can_run(make_task(target=target)) is False


@pytest.mark.asyncio
async def test_can_run_false_when_telescope_not_ready() -> None:
    script = make_script()
    telescope = make_telescope(ready=False)
    script._comm.has_proxy = AsyncMock(return_value=True)
    script._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))
    target = SiderealTarget(name="Vega", ra=279.23, dec=38.78)
    assert await script.can_run(make_task(target=target)) is False


# ── run ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_raises_when_no_data() -> None:
    script = make_script()
    await script.run(None)  # should return without error


@pytest.mark.asyncio
async def test_run_raises_when_no_target() -> None:
    script = make_script()
    data = make_task(target=None)
    with pytest.raises(ValueError, match="No target"):
        await script.run(data)


@pytest.mark.asyncio
async def test_run_moves_telescope_and_focuses() -> None:
    script = make_script(count=3, step=0.1, exposure_time=2.0)
    telescope = make_telescope()
    autofocus = make_autofocus()

    # proxy is called twice: (telescope, IPointingRaDec) then (autofocus, IAutoFocus)
    script._comm.proxy = MagicMock(side_effect=[make_proxy_cm(telescope), make_proxy_cm(autofocus)])
    # safe_proxy is called once in finally: (telescope, IMotion)
    script._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))

    target = SiderealTarget(name="Vega", ra=279.23, dec=38.78)
    data = make_task(target=target)

    await script.run(data)

    telescope.move_radec.assert_called_once()
    autofocus.auto_focus.assert_called_once_with(3, 0.1, 2.0)


@pytest.mark.asyncio
async def test_run_stops_telescope_in_finally() -> None:
    """Telescope is stopped even if auto_focus raises."""
    script = make_script()
    telescope = make_telescope()
    autofocus = make_autofocus()
    autofocus.auto_focus = AsyncMock(side_effect=RuntimeError("focus failed"))

    script._comm.proxy = MagicMock(side_effect=[make_proxy_cm(telescope), make_proxy_cm(autofocus)])
    script._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))

    target = SiderealTarget(name="Vega", ra=279.23, dec=38.78)
    data = make_task(target=target)

    with pytest.raises(RuntimeError):
        await script.run(data)

    # ITelescope always implements IMotion, so stop_motion is always called
    telescope.stop_motion.assert_called_once()


# ── estimate_duration ────────────────────────────────────────────────────────


def test_estimate_duration_falls_back_without_capabilities() -> None:
    script = make_script(count=3, exposure_time=2.0)
    assert script.estimate_duration(None) == 3 * 2.0 + 60.0


def test_estimate_duration_uses_real_slew_rate_when_available() -> None:
    script = make_script(count=3, exposure_time=2.0)
    telescope_capability = TelescopeCapability(module_name="telescope", slew_rate_deg_per_s=3.0)
    capabilities = InstrumentCapabilities([Instrument(telescope=telescope_capability)])
    data = TaskData(task=MagicMock(), instrument_capabilities=capabilities)

    duration = script.estimate_duration(data)
    slew_time = telescope_capability.estimate_slew_time_s()
    assert slew_time is not None

    assert duration == 3 * 2.0 + slew_time
    assert duration != 3 * 2.0 + 60.0  # sanity: the real rate actually changed the estimate


def test_estimate_duration_falls_back_when_telescope_module_not_matched() -> None:
    script = make_script(count=3, exposure_time=2.0)
    capabilities = InstrumentCapabilities(
        [Instrument(telescope=TelescopeCapability(module_name="a-different-telescope", slew_rate_deg_per_s=3.0))]
    )
    data = TaskData(task=MagicMock(), instrument_capabilities=capabilities)

    assert script.estimate_duration(data) == 3 * 2.0 + 60.0
