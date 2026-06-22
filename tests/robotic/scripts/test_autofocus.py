from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.robotic.scripts.imaging.autofocus import AutoFocusScript
from pyobs.robotic.task import TaskData


def make_script(**kwargs) -> AutoFocusScript:
    s = AutoFocusScript(**kwargs)
    s._comm = MagicMock()
    return s


def make_task(target=None) -> TaskData:
    task = MagicMock()
    task.target = target
    return TaskData(task=task)


def make_telescope(ready=True, is_motion=True) -> MagicMock:
    from pyobs.interfaces import IMotion, IPointingRaDec, ITelescope

    interfaces = [IPointingRaDec, ITelescope]
    if is_motion:
        interfaces.append(IMotion)

    tel = MagicMock(spec=interfaces)
    tel.is_ready = AsyncMock(return_value=ready)
    tel.move_radec = AsyncMock()
    tel.stop_motion = AsyncMock()
    tel.__class__ = type("Telescope", tuple(interfaces), {})
    return tel


def make_autofocus() -> MagicMock:
    from pyobs.interfaces import IAutoFocus

    af = MagicMock(spec=[IAutoFocus])
    af.auto_focus = AsyncMock()
    return af


def make_proxy_cm(value: object) -> MagicMock:
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=value)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


# ── can_run ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_can_run_true_when_ready() -> None:
    script = make_script()
    telescope = make_telescope(ready=True)
    script._comm.has_proxy = AsyncMock(return_value=True)
    script._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))
    assert await script.can_run(None) is True


@pytest.mark.asyncio
async def test_can_run_false_when_autofocus_unavailable() -> None:
    script = make_script()
    script._comm.has_proxy = AsyncMock(return_value=False)
    assert await script.can_run(None) is False


@pytest.mark.asyncio
async def test_can_run_false_when_telescope_not_ready() -> None:
    script = make_script()
    telescope = make_telescope(ready=False)
    script._comm.has_proxy = AsyncMock(return_value=True)
    script._comm.safe_proxy = MagicMock(return_value=make_proxy_cm(telescope))
    assert await script.can_run(None) is False


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
