from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import astropy.units as u
import pytest
from astropy.time import TimeDelta

from pyobs.robotic import Task
from pyobs.robotic.scheduler.merits.transit import TransitMerit
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.robotic.scripts.imaging.imaging import Configuration, InstrumentConfig
from pyobs.robotic.scripts.imaging.transitimaging import TransitImagingScript
from pyobs.robotic.task import TaskData
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time

# ── helpers ───────────────────────────────────────────────────────────────────


def make_script() -> TransitImagingScript:
    config = Configuration(
        instrument_configs=[InstrumentConfig(exposure_time=30.0, image_type=ImageType.OBJECT)],
        repeats=1,
    )
    script = TransitImagingScript(camera="camera", configuration=config)
    script._comm = MagicMock()
    return script


def make_transit_merit(duration: int = 3600, ingress: float = 0.2) -> TransitMerit:
    # jd0 set to a recent transit mid-point
    now = Time.now()
    # place mid-transit 1 hour in the future so we're in the ingress window
    jd0 = now.jd + 1.0 / 24.0
    return TransitMerit(jd0=jd0, period=10.0, duration=duration, ingress=ingress)


def make_task_data(merit: TransitMerit | None = None) -> TaskData:
    merits = [merit] if merit is not None else []
    task = Task(
        id=1,
        name="transit_task",
        duration=3600,
        merits=merits,
        target=SiderealTarget(name="WASP-12", ra=97.637, dec=29.672),
    )
    data = MagicMock()
    data.task = task
    return data


# ── can_run ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_can_run_false_without_transit_merit() -> None:
    """Verifies TransitImagingScript adds the TransitMerit check on top of base class."""
    script = make_script()
    with patch.object(script.__class__.__bases__[0], "can_run", AsyncMock(return_value=True)):
        data = make_task_data(merit=None)
        assert await script.can_run(data) is False
        assert "TransitMerit" in script.cant_run_reason()


# ── run / _run_configurations ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_raises_without_transit_merit() -> None:
    script = make_script()
    data = make_task_data(merit=None)
    with pytest.raises(ValueError, match="TransitMerit"):
        await script.run(data)


@pytest.mark.asyncio
async def test_run_configurations_loops_until_end_time() -> None:
    """_run_configurations runs at least once and stops after end_time passes."""
    script = make_script()
    merit = make_transit_merit(duration=3600, ingress=0.2)
    script._transit_merit = merit

    fixed_end_time = merit.end_time()
    run_count = 0

    async def mock_run_configuration(repeat, target, track):
        nonlocal run_count
        run_count += 1

    script._run_configuration = mock_run_configuration

    # Time.now returns before end_time on first call, after on second
    call_count = 0

    def controlled_now():
        nonlocal call_count
        call_count += 1
        if call_count <= 1:
            return fixed_end_time - TimeDelta(60 * u.second)
        return fixed_end_time + TimeDelta(60 * u.second)

    with patch.object(TransitMerit, "end_time", return_value=fixed_end_time):
        with patch("pyobs.robotic.scripts.imaging.transitimaging.Time.now", side_effect=controlled_now):
            await script._run_configurations(None, asyncio.Future())

    assert run_count == 1


@pytest.mark.asyncio
async def test_run_configurations_stops_immediately_if_past_end_time() -> None:
    """_run_configurations does not run at all if end_time is already past."""
    script = make_script()
    merit = make_transit_merit()
    script._transit_merit = merit

    # end_time already passed
    past_end_time = Time.now() - TimeDelta(60 * u.second)

    run_count = 0

    async def mock_run_configuration(repeat, target, track):
        nonlocal run_count
        run_count += 1

    script._run_configuration = mock_run_configuration

    with patch.object(TransitMerit, "end_time", return_value=past_end_time):
        await script._run_configurations(None, asyncio.Future())

    assert run_count == 0


@pytest.mark.asyncio
async def test_run_configurations_raises_without_merit() -> None:
    script = make_script()
    script._transit_merit = None
    with pytest.raises(ValueError, match="TransitMerit"):
        await script._run_configurations(None, asyncio.Future())


@pytest.mark.asyncio
async def test_run_configurations_uses_modulo_repeats() -> None:
    """repeat index wraps around configuration.repeats."""
    config = Configuration(
        instrument_configs=[InstrumentConfig(exposure_time=10.0, image_type=ImageType.OBJECT)],
        repeats=2,
    )
    script = TransitImagingScript(camera="camera", configuration=config)
    script._comm = MagicMock()
    merit = make_transit_merit()
    script._transit_merit = merit

    seen_repeats = []

    async def mock_run_configuration(repeat, target, track):
        seen_repeats.append(repeat)
        await asyncio.sleep(0)

    script._run_configuration = mock_run_configuration

    # compute end_time before patching to avoid recursion
    fixed_end_time = merit.end_time()
    past_end = fixed_end_time + TimeDelta(1 * u.second)
    call_count = 0

    def advancing_now():
        nonlocal call_count
        call_count += 1
        if call_count > 3:
            return past_end
        return fixed_end_time - TimeDelta(1 * u.hour)

    with patch("pyobs.robotic.scripts.imaging.transitimaging.Time.now", side_effect=advancing_now):
        with patch.object(TransitMerit, "end_time", return_value=fixed_end_time):
            await script._run_configurations(None, asyncio.Future())

    # repeats should cycle through 0, 1, 0 (modulo 2)
    assert seen_repeats == [0, 1, 0]
