import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.robotic import Task
from pyobs.robotic.scheduler import DataProvider
from pyobs.robotic.scheduler.merits import ConstantMerit, TimeWindowMerit
from pyobs.robotic.scheduler.meritscheduler import (
    find_next_best_task,
    evaluate_merits,
    check_for_better_task,
    schedule_in_interval,
)
from pyobs.utils.time import Time
from .task import TestTask


def test_evaluate_merits() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    start = Time.now()
    end = start + TimeDelta(5000 * u.second)

    tasks: list[Task] = [
        TestTask(1, "1", 100, merits=[ConstantMerit(10)]),
        TestTask(1, "1", 100, merits=[ConstantMerit(5)]),
    ]
    merits = evaluate_merits(tasks, start, end, data)

    assert merits == [10.0, 5.0]


@pytest.mark.asyncio
async def test_next_best_task() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    start = Time.now()
    end = start + TimeDelta(5000)

    # two constant merits
    tasks: list[Task] = [
        TestTask(1, "1", 100, merits=[ConstantMerit(10)]),
        TestTask(1, "1", 100, merits=[ConstantMerit(5)]),
    ]
    best, merit = find_next_best_task(tasks, start, end, data)
    assert best == tasks[0]
    assert merit == 10.0

    # one merit will increase and beat the first best
    tasks = [
        TestTask(
            1,
            "1",
            4000,
            merits=[
                ConstantMerit(10),
                TimeWindowMerit(
                    [{"start": start + TimeDelta(1000 * u.second), "end": start + TimeDelta(2000 * u.second)}]
                ),
            ],
        ),
        TestTask(1, "1", 4000, merits=[ConstantMerit(5)]),
    ]
    best, merit = find_next_best_task(tasks, start, end, data)
    assert best == tasks[1]
    assert merit == 5.0


def test_check_for_better_task() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    start = Time.now()
    end = start + TimeDelta(5000)

    # at the beginning, tasks[1] will be better (5), but after 1000 seconds tasks[0] will beat it (10)
    tasks: list[Task] = [
        TestTask(
            1,
            "1",
            4000,
            merits=[
                ConstantMerit(10),
                TimeWindowMerit(
                    [{"start": start + TimeDelta(1000 * u.second), "end": start + TimeDelta(2000 * u.second)}]
                ),
            ],
        ),
        TestTask(1, "1", 4000, merits=[ConstantMerit(5)]),
    ]
    better, time, merit = check_for_better_task(tasks[1], 5.0, tasks, start, end, data)
    assert better == tasks[0]
    assert time >= start + TimeDelta(1000 * u.second)
    assert merit == 10.0


@pytest.mark.asyncio
async def test_fill_for_better_task() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    start = Time("2025-11-01 00:00:00")
    end = start + TimeDelta(3600 * u.second)
    after_start = start + TimeDelta(600 * u.second)
    after_end = start + TimeDelta(900 * u.second)

    # at the beginning, tasks 2 will be better (5), but after 600 seconds tasks 1 will beat it (10)
    # then the scheduler tries to fill the hole and should schedule task 3 first
    # task 2 will only be scheduled afterward
    tasks: list[Task] = [
        TestTask(1, "1", 1800, merits=[ConstantMerit(10), TimeWindowMerit([{"start": after_start, "end": after_end}])]),
        TestTask(2, "2", 1800, merits=[ConstantMerit(5)]),
        TestTask(3, "3", 300, merits=[ConstantMerit(1)]),
    ]

    # note that task 1 will not be scheduled exactly at its start time
    schedule = schedule_in_interval(tasks, start, end, data, step=10)
    scheduled_task = await anext(schedule)
    assert scheduled_task.task.id == 1
    assert scheduled_task.start >= after_start

    # task 3 fills the hole before task 1
    scheduled_task = await anext(schedule)
    assert scheduled_task.task.id == 3
    assert scheduled_task.start == start


@pytest.mark.asyncio
async def test_postpone_task() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    start = Time("2025-11-01 00:00:00")
    end = start + TimeDelta(3600 * u.second)
    after_start = start + TimeDelta(600 * u.second)
    after_end = start + TimeDelta(1800 * u.second)

    # at the beginning, tasks 2 will be better (5), but after 600 seconds tasks 1 will beat it (10)
    # in contrast to test_fill_for_better_task the after_end time here is longer, so the scheduler should just
    # postpone task 1 by a bit, then schedule task 2 afterward
    tasks: list[Task] = [
        TestTask(1, "1", 1800, merits=[ConstantMerit(10), TimeWindowMerit([{"start": after_start, "end": after_end}])]),
        TestTask(2, "2", 1800, merits=[ConstantMerit(5)]),
        TestTask(3, "3", 300, merits=[ConstantMerit(1)]),
    ]
    schedule = schedule_in_interval(tasks, start, end, data, step=10)

    # task 2 will be scheduled exactly at its start time
    scheduled_task = await anext(schedule)
    assert scheduled_task.task.id == 2
    assert scheduled_task.start == start

    # task 1 after that
    scheduled_task = await anext(schedule)
    assert scheduled_task.task.id == 1
    assert scheduled_task.start >= after_start

    # let's try this again with a sorted list
    schedule2 = sorted([i async for i in schedule_in_interval(tasks, start, end, data, step=10)], key=lambda x: x.start)
    assert schedule2[0].task.id == 2
    assert schedule2[1].task.id == 1
