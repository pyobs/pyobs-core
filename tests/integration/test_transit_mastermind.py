from __future__ import annotations

import asyncio
from unittest.mock import patch

import astropy.units as u
import pytest
from astropy.time import TimeDelta

from pyobs.robotic import Task
from pyobs.robotic.observation import Observation, ObservationList, ObservationState
from pyobs.robotic.scheduler.merits.transit import TransitMerit
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.robotic.scripts.imaging.imaging import Configuration, InstrumentConfig
from pyobs.robotic.scripts.imaging.transitimaging import TransitImagingScript
from pyobs.utils.enums import ImageType
from pyobs.utils.time import Time
from tests.integration.test_mastermind import (
    NIGHT,
    FailingRunner,
    QuickRunner,
    make_mastermind,
    run_until_state,
)
from tests.integration.test_scheduler_mastermind import make_obs_archive

# ── transit parameters ────────────────────────────────────────────────────────
# Mid-transit exactly at NIGHT: jd0 = NIGHT.jd, period = 1.0 day
# With duration=3600s and ingress=0.2, end_time = NIGHT + 42 minutes

TRANSIT_JD0 = NIGHT.jd  # mid-transit at NIGHT
TRANSIT_PERIOD = 1.0  # days
TRANSIT_DURATION = 3600  # seconds
TRANSIT_INGRESS = 0.2  # fraction of duration


def make_transit_merit() -> TransitMerit:
    return TransitMerit(
        jd0=TRANSIT_JD0,
        period=TRANSIT_PERIOD,
        duration=TRANSIT_DURATION,
        ingress=TRANSIT_INGRESS,
    )


def make_transit_task() -> Task:
    merit = make_transit_merit()
    return Task(
        id=1,
        name="transit_task",
        duration=TRANSIT_DURATION,
        target=SiderealTarget(name="WASP-12b", ra=97.637, dec=29.672),
        merits=[merit],
    )


def make_transit_observation(task: Task) -> Observation:
    """Create a transit observation scheduled around NIGHT."""
    merit = next(m for m in task.merits if isinstance(m, TransitMerit))
    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        end_time = merit.end_time()
    return Observation(
        task=task,
        start=NIGHT,
        end=end_time,
        state=ObservationState.PENDING,
    )


class TransitQuickRunner(QuickRunner):
    """Runner that immediately completes, simulating transit script execution."""

    def __init__(self, end_time: Time):
        super().__new__(type(self))
        self._comm = None
        self._observer = None
        self._vfs = None
        self._timezone = None
        self._location = None
        self.observation_archive = None
        self.task_archive = None
        self._end_time = end_time

    async def run_task(self, task: Task) -> bool:
        """Simulate transit imaging: run until end_time."""
        await asyncio.sleep(0.05)
        return True


# ── transit merit → end_time ──────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_transit_merit_end_time_after_night() -> None:
    """TransitMerit.end_time() is after NIGHT when mid-transit is at NIGHT."""
    merit = make_transit_merit()
    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        end_time = merit.end_time()
    assert end_time > NIGHT


@pytest.mark.asyncio
@pytest.mark.integration
async def test_transit_merit_end_time_offset() -> None:
    """end_time = NIGHT + (duration/2 + ingress*duration) seconds."""
    merit = make_transit_merit()
    expected_offset = TimeDelta((TRANSIT_DURATION / 2.0 + TRANSIT_INGRESS * TRANSIT_DURATION) * u.second)
    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        end_time = merit.end_time()
    delta = (end_time - NIGHT).to(u.second).value
    expected = expected_offset.to(u.second).value
    assert abs(delta - expected) < 120.0  # within 2 minutes (barycentric correction shifts by ~70s)


# ── mastermind runs transit observation ───────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_completes_transit_observation() -> None:
    """Mastermind picks up a transit observation and runs it to completion."""
    task = make_transit_task()
    obs = make_transit_observation(task)

    obs_archive = make_obs_archive()
    await obs_archive.add_observations(ObservationList([obs]))

    mm = make_mastermind(obs_archive)
    reached = await run_until_state(mm, obs_archive, ObservationState.COMPLETED, timeout=10.0)
    assert reached, "Mastermind did not complete the transit observation"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mastermind_marks_failed_transit_observation() -> None:
    """Mastermind marks transit observation FAILED when runner raises."""
    task = make_transit_task()
    obs = make_transit_observation(task)

    obs_archive = make_obs_archive()
    await obs_archive.add_observations(ObservationList([obs]))

    mm = make_mastermind(obs_archive, runner=FailingRunner())
    reached = await run_until_state(mm, obs_archive, ObservationState.FAILED, timeout=10.0)
    assert reached, "Mastermind did not mark transit observation as FAILED"


# ── TransitImagingScript stops at end_time ────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.integration
async def test_transit_script_runs_until_end_time() -> None:
    """TransitImagingScript._run_configurations loops until merit.end_time()."""
    from unittest.mock import MagicMock

    config = Configuration(
        instrument_configs=[InstrumentConfig(exposure_time=10.0, image_type=ImageType.OBJECT)],
        repeats=1,
    )
    script = TransitImagingScript(camera="camera", configuration=config)
    script._comm = MagicMock()

    merit = make_transit_merit()
    script._transit_merit = merit

    run_count = 0

    async def mock_run_configuration(repeat, target, track):
        nonlocal run_count
        run_count += 1

    script._run_configuration = mock_run_configuration

    # Time.now starts before end_time, advances past it after one iteration
    call_count = 0
    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        fixed_end = merit.end_time()

    def advancing_now():
        nonlocal call_count
        call_count += 1
        if call_count <= 1:
            return NIGHT  # before end_time
        return fixed_end + TimeDelta(60 * u.second)  # after end_time

    with patch("pyobs.robotic.scripts.imaging.transitimaging.Time.now", side_effect=advancing_now):
        with patch.object(TransitMerit, "end_time", return_value=fixed_end):
            await script._run_configurations(None, asyncio.Future())

    assert run_count == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_transit_script_does_not_run_after_end_time() -> None:
    """TransitImagingScript does not run if end_time has already passed."""
    from unittest.mock import MagicMock

    config = Configuration(
        instrument_configs=[InstrumentConfig(exposure_time=10.0, image_type=ImageType.OBJECT)],
        repeats=1,
    )
    script = TransitImagingScript(camera="camera", configuration=config)
    script._comm = MagicMock()

    merit = make_transit_merit()
    script._transit_merit = merit

    run_count = 0

    async def mock_run_configuration(repeat, target, track):
        nonlocal run_count
        run_count += 1

    script._run_configuration = mock_run_configuration

    with patch("pyobs.utils.time.Time.now", return_value=NIGHT):
        fixed_end = merit.end_time()

    # end_time is already in the past relative to now
    past_end = fixed_end - TimeDelta(600 * u.second)

    with patch(
        "pyobs.robotic.scripts.imaging.transitimaging.Time.now", return_value=fixed_end + TimeDelta(60 * u.second)
    ):
        with patch.object(TransitMerit, "end_time", return_value=past_end):
            await script._run_configurations(None, asyncio.Future())

    assert run_count == 0
