import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import TimeDelta
import astropy.units as u

from pyobs.robotic import Task
from pyobs.robotic.scheduler import DataProvider
from pyobs.robotic.scheduler.merits import ConstantMerit, TimeWindowMerit
from pyobs.robotic.scheduler.meritscheduler import find_next_best_task, evaluate_merits, check_for_better_task
from pyobs.utils.time import Time
from .task import TestTask


def test_evaluate_merits() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    start = Time.now()
    end = start + TimeDelta(5000)

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
    better, time = check_for_better_task(tasks[1], 5.0, tasks, start, end, data)
    assert better == tasks[0]
    assert time >= start + TimeDelta(1000 * u.second)
