import asyncio
import time as time_module

import astropy.units as u
import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import TimeDelta

from pyobs.robotic import Task
from pyobs.robotic.instruments import InstrumentCapabilities
from pyobs.robotic.scheduler import DataProvider
from pyobs.robotic.scheduler.constraints import Constraint
from pyobs.robotic.scheduler.merits import ConstantMerit, TimeWindowMerit
from pyobs.robotic.scheduler.merits.timewindow import TimeWindow
from pyobs.robotic.scheduler.ondemandscheduler import OnDemandScheduler
from pyobs.robotic.scripts import Script
from pyobs.robotic.task import TaskData
from pyobs.utils.time import Time


class _CapabilitiesEchoingScript(Script):
    """Returns 1.0 if TaskData.instrument_capabilities was forwarded, else 0.0 -- used to check
    that instrument_capabilities reaches Task.estimate_duration() through the scheduler's call
    chain, without needing a real InstrumentCapabilities instance at every layer."""

    def estimate_duration(self, data: TaskData | None = None, time: Time | None = None) -> float:
        if data is not None and data.instrument_capabilities is not None:
            return 1.0
        return 0.0


@pytest.mark.asyncio
async def test_evaluate_merits() -> None:
    scheduler = OnDemandScheduler()
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    start = Time.now()
    end = start + TimeDelta(5000 * u.day)

    tasks: list[Task] = [
        Task(id=1, name="1", duration=100, merits=[ConstantMerit(merit=10)]),
        Task(id=1, name="1", duration=100, merits=[ConstantMerit(merit=5)]),
    ]
    merits = await scheduler.evaluate_constraints_and_merits(tasks, {}, start, end, data)

    assert merits == [10.0, 5.0]


@pytest.mark.asyncio
async def test_next_best_task() -> None:
    scheduler = OnDemandScheduler()
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    start = Time.now()
    end = start + TimeDelta(5000 * u.day)

    # two constant merits
    tasks: list[Task] = [
        Task(id=1, name="1", duration=100, merits=[ConstantMerit(merit=10)]),
        Task(id=1, name="1", duration=100, merits=[ConstantMerit(merit=5)]),
    ]
    best, merit = await scheduler.find_next_best_task(tasks, {}, start, end, data)
    assert best == tasks[0]
    assert merit == 10.0

    # one merit will increase and beat the first best
    tasks = [
        Task(
            id=1,
            name="1",
            duration=4000,
            merits=[
                ConstantMerit(merit=10),
                TimeWindowMerit(
                    windows=[
                        TimeWindow(start=start + TimeDelta(1000 * u.second), end=start + TimeDelta(2000 * u.second))
                    ]
                ),
            ],
        ),
        Task(id=2, name="2", duration=4000, merits=[ConstantMerit(merit=5)]),
    ]
    best, merit = await scheduler.find_next_best_task(tasks, {}, start, end, data)
    assert best == tasks[1]
    assert merit == 5.0


@pytest.mark.asyncio
async def test_check_for_better_task() -> None:
    scheduler = OnDemandScheduler()
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    start = Time.now()
    end = start + TimeDelta(5000 * u.day)

    # at the beginning, tasks[1] will be better (5), but after 1000 seconds tasks[0] will beat it (10)
    tasks: list[Task] = [
        Task(
            id=1,
            name="1",
            duration=4000,
            merits=[
                ConstantMerit(merit=10),
                TimeWindowMerit(
                    windows=[
                        TimeWindow(start=start + TimeDelta(1000 * u.second), end=start + TimeDelta(2000 * u.second))
                    ]
                ),
            ],
        ),
        Task(id=2, name="2", duration=4000, merits=[ConstantMerit(merit=5)]),
    ]
    better, time, merit = await scheduler.check_for_better_task(tasks[1], {}, 5.0, tasks, start, end, data)
    assert better == tasks[0]
    assert time >= start + TimeDelta(1000 * u.second)
    assert merit == 10.0


@pytest.mark.asyncio
async def test_fill_for_better_task() -> None:
    scheduler = OnDemandScheduler()
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    start = Time("2025-11-01 00:00:00")
    end = start + TimeDelta(3600 * u.second)
    after_start = start + TimeDelta(600 * u.second)
    after_end = start + TimeDelta(900 * u.second)

    # at the beginning, tasks 2 will be better (5), but after 600 seconds tasks 1 will beat it (10)
    # then the scheduler tries to fill the hole and should schedule task 3 first
    # task 2 will only be scheduled afterward
    tasks: list[Task] = [
        Task(
            id=1,
            name="1",
            duration=1800,
            merits=[ConstantMerit(merit=10), TimeWindowMerit(windows=[TimeWindow(start=after_start, end=after_end)])],
        ),
        Task(id=2, name="2", duration=1800, merits=[ConstantMerit(merit=5)]),
        Task(id=3, name="3", duration=300, merits=[ConstantMerit(merit=1)]),
    ]

    # note that task 1 will not be scheduled exactly at its start time
    schedule = scheduler.schedule_first_in_interval(tasks, {}, start, end, data, step=10)
    scheduled_task = await anext(schedule)
    assert scheduled_task.task.id == 1
    assert scheduled_task.start >= after_start

    # task 3 fills the hole before task 1
    scheduled_task = await anext(schedule)
    assert scheduled_task.task.id == 3
    assert scheduled_task.start == start


@pytest.mark.asyncio
async def test_postpone_task() -> None:
    scheduler = OnDemandScheduler()
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    start = Time("2025-11-01 00:00:00")
    end = start + TimeDelta(3600 * u.second)
    after_start = start + TimeDelta(600 * u.second)
    after_end = start + TimeDelta(1800 * u.second)

    # at the beginning, tasks 2 will be better (5), but after 600 seconds tasks 1 will beat it (10)
    # in contrast to test_fill_for_better_task the after_end time here is longer, so the scheduler should just
    # postpone task 1 by a bit, then schedule task 2 afterward
    tasks: list[Task] = [
        Task(
            id=1,
            name="1",
            duration=1800,
            merits=[ConstantMerit(merit=10), TimeWindowMerit(windows=[TimeWindow(start=after_start, end=after_end)])],
        ),
        Task(id=2, name="2", duration=1800, merits=[ConstantMerit(merit=5)]),
        Task(id=3, name="3", duration=300, merits=[ConstantMerit(merit=1)]),
    ]
    schedule = scheduler.schedule_first_in_interval(tasks, {}, start, end, data, step=10)

    # task 2 will be scheduled exactly at its start time
    scheduled_task = await anext(schedule)
    assert scheduled_task.task.id == 2
    assert scheduled_task.start == start

    # task 1 after that
    scheduled_task = await anext(schedule)
    assert scheduled_task.task.id == 1
    assert scheduled_task.start >= after_start

    # let's try this again with a sorted list
    schedule2 = sorted(
        [i async for i in scheduler.schedule_first_in_interval(tasks, {}, start, end, data, step=10)],
        key=lambda x: x.start,
    )
    assert schedule2[0].task.id == 2
    assert schedule2[1].task.id == 1


# ── event-loop responsiveness during constraint/merit evaluation ────────────


class SleepyConstraint(Constraint):
    """Test-only constraint that simulates CPU-bound work with a blocking sleep."""

    seconds: float = 0.05

    def to_astroplan(self):  # type: ignore[override]
        raise NotImplementedError

    async def __call__(self, time: Time, task: Task, data: DataProvider) -> bool:
        time_module.sleep(self.seconds)
        return True


async def _run_with_heartbeat(coro):
    """Runs coro concurrently with a fast heartbeat, returns (coro's result, heartbeat count)."""
    stop = asyncio.Event()
    heartbeats = 0

    async def heartbeat() -> None:
        nonlocal heartbeats
        while not stop.is_set():
            await asyncio.sleep(0.02)
            heartbeats += 1

    async def run_and_stop():
        result = await coro
        stop.set()
        return result

    result, _ = await asyncio.gather(run_and_stop(), heartbeat())
    return result, heartbeats


@pytest.mark.asyncio
async def test_find_next_best_task_does_not_block_event_loop() -> None:
    scheduler = OnDemandScheduler()
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    start = Time.now()
    end = start + TimeDelta(5000 * u.day)

    tasks: list[Task] = [
        Task(
            id=1, name="1", duration=100, constraints=[SleepyConstraint(seconds=0.05)], merits=[ConstantMerit(merit=10)]
        ),
        Task(
            id=2, name="2", duration=100, constraints=[SleepyConstraint(seconds=0.05)], merits=[ConstantMerit(merit=5)]
        ),
    ]

    (best, merit), heartbeats = await _run_with_heartbeat(scheduler.find_next_best_task(tasks, {}, start, end, data))

    assert best == tasks[0]
    assert merit == 10.0
    # ~0.1s of blocking constraint evaluation at a 0.02s heartbeat cadence: the loop should have
    # kept ticking throughout if (and only if) the evaluation was actually offloaded.
    assert heartbeats >= 2


@pytest.mark.asyncio
async def test_can_postpone_task_does_not_block_event_loop() -> None:
    scheduler = OnDemandScheduler()
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    start = Time("2025-11-01T00:00:00", scale="utc")
    end = start + TimeDelta(3600 * u.second)

    task = Task(id=1, name="1", duration=100, merits=[ConstantMerit(merit=10)])
    better_task = Task(
        id=2, name="2", duration=100, constraints=[SleepyConstraint(seconds=0.05)], merits=[ConstantMerit(merit=20)]
    )

    coro = scheduler.can_postpone_task(task, {}, better_task, 20.0, start, end, data)
    postpone_time, heartbeats = await _run_with_heartbeat(coro)

    assert postpone_time is not None
    assert heartbeats >= 2


@pytest.mark.asyncio
async def test_check_for_better_task_does_not_block_event_loop() -> None:
    scheduler = OnDemandScheduler()
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    data = DataProvider(observer)
    start = Time.now()
    end = start + TimeDelta(5000 * u.day)

    # small step count (duration 150, step 50 -> 3 iterations) to keep the test fast while still
    # exercising check_for_better_task's internal loop, each iteration offloading one evaluation
    tasks: list[Task] = [
        Task(
            id=1,
            name="1",
            duration=150,
            constraints=[SleepyConstraint(seconds=0.05)],
            merits=[
                ConstantMerit(merit=10),
                TimeWindowMerit(windows=[TimeWindow(start=start + TimeDelta(100 * u.second), end=end)]),
            ],
        ),
        Task(id=2, name="2", duration=150, merits=[ConstantMerit(merit=5)]),
    ]

    coro = scheduler.check_for_better_task(tasks[1], {}, 5.0, tasks, start, end, data, step=50)
    (better, better_time, better_merit), heartbeats = await _run_with_heartbeat(coro)

    assert better == tasks[0]
    assert heartbeats >= 4


def test_create_scheduled_task_forwards_instrument_capabilities() -> None:
    scheduler = OnDemandScheduler()
    start = Time.now()
    task = Task(
        id=1,
        name="1",
        duration=100,
        script={"class": "tests.robotic.scheduler.test_ondemandscheduler._CapabilitiesEchoingScript"},
    )

    without_caps = scheduler.create_scheduled_task(task, merit=1.0, time=start)
    assert (without_caps.end - without_caps.start).sec == pytest.approx(0.0)

    with_caps = scheduler.create_scheduled_task(
        task, merit=1.0, time=start, instrument_capabilities=InstrumentCapabilities([])
    )
    assert (with_caps.end - with_caps.start).sec == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_schedule_threads_instrument_capabilities_end_to_end() -> None:
    """schedule() is the only entry point pyobs/modules/robotic/scheduler.py calls -- confirm
    instrument_capabilities makes it all the way from there down to Task.estimate_duration()."""
    observer = Observer(
        location=EarthLocation.from_geodetic(lon=20.8108 * u.deg, lat=-32.3758 * u.deg, height=1798 * u.m)
    )
    scheduler = OnDemandScheduler(observer=observer)
    start = Time.now()
    # short window -- the echoing script's 1s duration means schedule() keeps finding a next
    # slot for the same task, so this only needs to be wide enough for one, not exhaustively long
    end = start + TimeDelta(2 * u.second)

    task = Task(
        id=1,
        name="1",
        duration=100,
        merits=[ConstantMerit(merit=10)],
        script={"class": "tests.robotic.scheduler.test_ondemandscheduler._CapabilitiesEchoingScript"},
    )

    observations = [
        obs
        async for obs in scheduler.schedule([task], [], start, end, instrument_capabilities=InstrumentCapabilities([]))
    ]

    assert len(observations) >= 1
    assert (observations[0].end - observations[0].start).sec == pytest.approx(1.0)
