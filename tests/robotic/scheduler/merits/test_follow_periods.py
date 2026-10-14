from __future__ import annotations

import asyncio
import datetime
import threading
from unittest.mock import AsyncMock

import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.utils import iers

from pyobs.robotic import Observation, Task
from pyobs.robotic.observation import ObservationList, ObservationState
from pyobs.robotic.scheduler import DataProvider
from pyobs.robotic.scheduler._executor import run_cpu_bound
from pyobs.robotic.scheduler.merits import ConstantMerit, FollowMerit, PerNightMerit
from pyobs.robotic.scheduler.observationarchiveevolution import ObservationArchiveEvolution
from pyobs.robotic.scheduler.ondemandscheduler import OnDemandScheduler
from pyobs.utils.time import Time


@pytest.fixture(autouse=True)
def offline_iers():
    with iers.conf.set_temp("auto_download", False), iers.conf.set_temp("auto_max_age", None):
        yield


def record(task, time, state=ObservationState.COMPLETED, end=None):
    return Observation(task=task, start=time, end=end or time + datetime.timedelta(minutes=5), state=state)


def make_archive(observer, records, mode="night"):
    archive = AsyncMock()
    original_loop = asyncio.get_running_loop()
    original_thread = threading.get_ident()
    evolution = ObservationArchiveEvolution(observer, archive, mode=mode)

    async def get_observations(**kwargs):
        assert not evolution._frozen
        assert threading.get_ident() == original_thread
        assert asyncio.get_running_loop() is original_loop
        if kwargs.get("task") is not None:
            kwargs["task_id"] = kwargs.pop("task").id
        return ObservationList(records).filter(**kwargs)

    archive.get_observations.side_effect = get_observations
    return evolution, archive


@pytest.mark.asyncio
async def test_reported_post_midnight_completion_and_previous_night_exclusion():
    observer = Observer(location=EarthLocation.from_geodetic(-70, -30, 200))
    follower = Task(id="darks", name="Darks", duration=300)
    current = record("lights", Time("2026-10-13T00:30:00"))
    old = record("lights", Time("2026-10-12T01:00:00"))
    for records, expected in [([current], 1.0), ([old], 0.0)]:
        evolution, archive = make_archive(observer, records)
        data = DataProvider(observer, evolution)
        time = Time("2026-10-13T03:00:00")
        merit = FollowMerit(task_id="lights")
        assert await merit(time, follower, data) == expected
        assert await merit(time, follower, data) == expected
        assert archive.get_observations.call_count == 1
        tomorrow = Time("2026-10-14T03:00:00")
        assert await merit(tomorrow, follower, data) == 0.0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode,longitude,latitude,stamp",
    [
        ("night", -70, -30, "2026-10-13T03:00:00"),
        ("night", 140, -30, "2026-10-13T03:00:00"),
        ("day", -70, -30, "2026-10-13T15:00:00"),
        ("day", 140, -30, "2026-10-13T15:00:00"),
        ("night", -76, 41.2, "2026-10-13T03:00:00"),
        ("night", 9.9445, 51.5606, "2026-10-13T03:00:00"),
        ("day", 9.9445, 51.5606, "2026-04-13T14:00:00"),
    ],
)
async def test_real_and_evolved_history_share_boundaries_and_merits(mode, longitude, latitude, stamp):
    observer = Observer(location=EarthLocation.from_geodetic(longitude, latitude, 200))
    prerequisite = Task(id="lights", name="Lights", duration=300)
    follower = Task(id="follow", name="Follow", duration=300)
    time = Time(stamp)
    empty = DataProvider(observer, mode=mode)
    start, end = empty.period_bounds(time)
    records = [
        record("lights", start - datetime.timedelta(minutes=1), end=start + datetime.timedelta(minutes=1)),
        record("lights", start),
        record("lights", end - datetime.timedelta(minutes=1), end=end + datetime.timedelta(minutes=1)),
        record("lights", end),
        record("unrelated", start),
        record("lights", start, state=ObservationState.FAILED),
    ]
    evolution, archive = make_archive(observer, records, mode)
    data = DataProvider(observer, evolution)
    key = data.night(time)
    await evolution.prefetch([prerequisite, follower], time, key)
    evolution.freeze()
    assert [o.start for o in await evolution.observations_for_night(key)] == [
        start,
        end - datetime.timedelta(minutes=1),
        start,
    ]
    follow = FollowMerit(task_id="lights")
    limit = PerNightMerit(count=2)
    assert await run_cpu_bound(follow, time, follower, data) == 1.0
    assert await run_cpu_bound(limit, time, prerequisite, data) == 0.0
    # The next cycle is empty after freeze, even when the inclusive backend query
    # returned its opening observation. Evolution then enables the new prerequisite.
    assert await run_cpu_bound(follow, end, follower, data) == 0.0
    assert await run_cpu_bound(limit, end, prerequisite, data) == 1.0  # only the opening record counts
    planned = record(prerequisite, end + datetime.timedelta(minutes=10))
    await evolution.evolve(planned, data.night(planned.start))
    assert await run_cpu_bound(follow, planned.end, follower, data) == 1.0
    assert await run_cpu_bound(follow, time, follower, data) == 1.0
    assert archive.get_observations.call_count == 3


@pytest.mark.asyncio
async def test_solar_morning_prerequisite_visible_in_afternoon_but_not_next_day():
    observer = Observer(location=EarthLocation.from_geodetic(20, 50, 200))
    records = [record("sun", Time("2026-10-13T08:00:00"))]
    evolution, _ = make_archive(observer, records, "day")
    data = DataProvider(observer, evolution)
    follower = Task(id="follow", name="Follow", duration=300)
    merit = FollowMerit(task_id="sun")
    assert await merit(Time("2026-10-13T14:00:00"), follower, data) == 1.0
    assert await merit(Time("2026-10-14T14:00:00"), follower, data) == 0.0


@pytest.mark.asyncio
async def test_standalone_evolve_date_only_and_no_archive():
    observer = Observer(location=EarthLocation.from_geodetic(-70, -30, 200))
    task = Task(id="a", name="A", duration=300)
    time = Time("2026-10-13T03:00:00")
    evolution, archive = make_archive(observer, [])
    data = DataProvider(observer, evolution)
    key = data.night(time)
    assert len(await evolution.observations_for_night(key)) == 0
    await evolution.evolve(record(task, time), key)
    assert await FollowMerit(task_id="a")(time, task, data) == 1.0
    assert archive.get_observations.call_count == 2
    no_archive = DataProvider(observer, mode="day")
    assert len(await no_archive.archive.observations_for_night(datetime.date(1900, 1, 1))) == 0
    with pytest.raises(ValueError, match="modes must match"):
        DataProvider(observer, evolution, mode="day")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode,longitude,latitude,stamp",
    [
        ("night", -70, -30, "2026-10-13T03:00:00"),
        ("day", -70, -30, "2026-10-13T15:00:00"),
        ("night", -76, 41.2, "2026-10-13T03:00:00"),
        ("night", 9.9445, 51.5606, "2026-10-13T03:00:00"),
        ("day", 9.9445, 51.5606, "2026-04-13T14:00:00"),
    ],
)
async def test_scheduler_propagates_mode_and_freezes_before_worker(mode, longitude, latitude, stamp, monkeypatch):
    observer = Observer(location=EarthLocation.from_geodetic(longitude, latitude, 200))
    time = Time(stamp)
    task = Task(id="lights", name="Lights", duration=300)
    evolution, archive = make_archive(observer, [record("lights", time - datetime.timedelta(minutes=10))], mode)
    scheduler = OnDemandScheduler(mode=mode)
    scheduler._observer = observer
    scheduler._obs_archive = archive
    seen = []

    async def schedule_in_interval(tasks, projects, start, end, data, **kwargs):
        assert data.archive._frozen
        assert data.archive.periods.mode == mode
        assert await run_cpu_bound(FollowMerit(task_id="lights"), start, task, data) == 1.0
        seen.append(data)
        yield record(task, start, state=ObservationState.PENDING)

    monkeypatch.setattr(scheduler, "schedule_in_interval", schedule_in_interval)
    result = [obs async for obs in scheduler.schedule([task], [], time, time + datetime.timedelta(hours=1))]
    assert len(result) == 1
    assert len(seen[0].archive._obs_for_night[seen[0].night(time)]) == 2
    assert archive.get_observations.call_count == 2
    query = archive.get_observations.call_args_list[-1].kwargs
    opening, closing = seen[0].period_bounds(time)
    assert query["start_after"] == opening
    assert query["start_before"] == closing


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode,latitude,longitude,stamp",
    [
        ("night", -30, -70, "2026-10-13T15:00:00"),
        ("day", -30, -70, "2026-10-13T15:00:00"),
        ("night", 51.5606, 9.9445, "2026-10-13T03:00:00"),
        ("day", 51.5606, 9.9445, "2026-04-13T14:00:00"),
    ],
)
async def test_full_schedule_resets_then_evolves_prerequisite_in_new_period(mode, latitude, longitude, stamp):
    observer = Observer(location=EarthLocation.from_geodetic(longitude, latitude, 200))
    data = DataProvider(observer, mode=mode)
    # Future scheduling starts shortly before a reset and spans into its next period.
    _, reset = data.period_bounds(Time(stamp))
    start = reset - datetime.timedelta(minutes=5)
    end = reset + datetime.timedelta(minutes=10)
    tasks = [
        Task(id="lights", name="Lights", duration=60, merits=[ConstantMerit(merit=10), PerNightMerit(count=1)]),
        Task(id="darks", name="Darks", duration=60, merits=[FollowMerit(task_id="lights"), PerNightMerit(count=1)]),
    ]
    scheduler = OnDemandScheduler(mode=mode)
    scheduler._observer = observer
    results = [obs async for obs in scheduler.schedule(tasks, [], start, end)]
    assert [obs.task_id for obs in results] == ["lights", "darks", "lights", "darks"]
    assert results[1].start < reset <= results[2].start


@pytest.mark.asyncio
async def test_wrong_evolved_key_cannot_pollute_cache():
    observer = Observer(location=EarthLocation.from_geodetic(-70, -30, 200))
    data = DataProvider(observer)
    time = Time("2026-10-13T03:00:00")
    task = Task(id="lights", name="Lights", duration=300)
    with pytest.raises(ValueError, match="period key"):
        await data.archive.evolve(record(task, time), data.night(time) + datetime.timedelta(days=1))
    assert data.archive._obs_for_task == {}
    assert data.archive._obs_for_night == {}
