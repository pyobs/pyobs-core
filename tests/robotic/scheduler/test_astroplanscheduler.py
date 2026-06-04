import pytest

from pyobs.robotic import Task
from pyobs.robotic.scheduler.astroplanscheduler import AstroplanScheduler
from pyobs.robotic.scheduler.constraints import AirmassConstraint
from pyobs.robotic.scheduler.merits import ConstantMerit
from pyobs.robotic.scheduler.targets import SiderealTarget
from pyobs.robotic.scheduler.targets.dynamictarget import DynamicTarget
from pyobs.robotic.scheduler.targets.picker.picker import Picker
from pyobs.utils.time import Time

# SAAO location
LOCATION = {"longitude": 20.8108, "latitude": -32.3758, "elevation": 1798.0}
TIMEZONE = "Africa/Johannesburg"

# A well-placed star from SAAO at night, and one never visible
BETELGEUSE = SiderealTarget(name="Betelgeuse", ra=83.82, dec=7.41)
POLARIS = SiderealTarget(name="Polaris", ra=37.95, dec=89.26)  # never visible from SAAO

# Night window: 2025-11-03 evening
START = Time("2025-11-03T20:00:00", scale="utc")
END = Time("2025-11-04T04:00:00", scale="utc")


@pytest.fixture
def scheduler() -> AstroplanScheduler:
    return AstroplanScheduler(
        twilight="astronomical",
        location=LOCATION,
        timezone=TIMEZONE,
    )


def make_task(name: str, target: SiderealTarget, duration: float = 300.0) -> Task:
    return Task(
        id=name,
        name=name,
        duration=duration,
        target=target,
        merits=[ConstantMerit(merit=1.0)],
    )


@pytest.mark.asyncio
async def test_schedules_single_task(scheduler: AstroplanScheduler) -> None:
    """A single visible task gets scheduled."""
    task = make_task("betelgeuse", BETELGEUSE)
    observations = [obs async for obs in scheduler.schedule([task], [], START, END)]

    assert len(observations) == 1
    assert observations[0].task.id == "betelgeuse"
    assert observations[0].start >= START
    assert observations[0].end <= END


class _EmptyPicker(Picker):
    async def __call__(self, time, task, data):
        return None


@pytest.mark.asyncio
async def test_does_not_schedule_non_sidereal_target(scheduler: AstroplanScheduler) -> None:
    """Task with DynamicTarget that resolves to None is skipped."""
    task = Task(
        id="dynamic",
        name="dynamic",
        duration=300.0,
        target=DynamicTarget(picker=_EmptyPicker()),
        merits=[ConstantMerit(merit=1.0)],
    )
    observations = [obs async for obs in scheduler.schedule([task], [], START, END)]
    assert len(observations) == 0


@pytest.mark.asyncio
async def test_schedules_multiple_tasks_by_priority(scheduler: AstroplanScheduler) -> None:
    """Higher priority task is scheduled earlier."""
    low = Task(id="low", name="low", duration=300.0, target=BETELGEUSE, priority=1.0, merits=[ConstantMerit(merit=1.0)])
    high = Task(
        id="high", name="high", duration=300.0, target=BETELGEUSE, priority=5.0, merits=[ConstantMerit(merit=1.0)]
    )

    observations = [obs async for obs in scheduler.schedule([low, high], [], START, END)]

    assert len(observations) == 2
    ids_in_order = [obs.task.id for obs in sorted(observations, key=lambda o: o.start)]
    assert ids_in_order[0] == "high"


@pytest.mark.asyncio
async def test_respects_airmass_constraint(scheduler: AstroplanScheduler) -> None:
    """Task with unsatisfiable airmass constraint is not scheduled."""
    task = Task(
        id="polaris",
        name="polaris",
        duration=300.0,
        target=POLARIS,
        constraints=[AirmassConstraint(max_airmass=2.0)],
        merits=[ConstantMerit(merit=1.0)],
    )
    observations = [obs async for obs in scheduler.schedule([task], [], START, END)]
    assert len(observations) == 0


@pytest.mark.asyncio
async def test_observation_times_within_window(scheduler: AstroplanScheduler) -> None:
    """All scheduled observations fall within the requested time window."""
    tasks = [
        make_task("star1", BETELGEUSE, duration=600.0),
        make_task("star2", SiderealTarget(name="Rigel", ra=78.63, dec=-8.20), duration=600.0),
    ]
    observations = [obs async for obs in scheduler.schedule(tasks, [], START, END)]

    for obs in observations:
        assert obs.start >= START, f"{obs.task.id} starts before window"
        assert obs.end <= END, f"{obs.task.id} ends after window"


class _FixedPicker(Picker):
    async def __call__(self, time, task, data):
        return BETELGEUSE


@pytest.mark.asyncio
async def test_dynamic_target_resolved_before_scheduling(scheduler: AstroplanScheduler) -> None:
    """DynamicTarget is resolved and scheduled as a SiderealTarget."""
    task = Task(
        id="dynamic",
        name="dynamic",
        duration=300.0,
        target=DynamicTarget(picker=_FixedPicker()),
        merits=[ConstantMerit(merit=1.0)],
    )
    observations = [obs async for obs in scheduler.schedule([task], [], START, END)]

    assert len(observations) == 1
    assert observations[0].task.id == "dynamic"


@pytest.mark.asyncio
async def test_abort_sets_event(scheduler: AstroplanScheduler) -> None:
    """abort() sets the internal abort event."""
    assert not scheduler._abort.is_set()
    await scheduler.abort()
    assert scheduler._abort.is_set()


@pytest.mark.asyncio
async def test_schedule_clears_abort_event(scheduler: AstroplanScheduler) -> None:
    """A new schedule() call clears any previous abort event."""
    await scheduler.abort()
    assert scheduler._abort.is_set()

    task = make_task("betelgeuse", BETELGEUSE)
    observations = [obs async for obs in scheduler.schedule([task], [], START, END)]

    # abort was cleared and scheduling completed normally
    assert len(observations) == 1
