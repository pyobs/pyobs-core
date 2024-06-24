import datetime
import multiprocessing
from typing import List, Any
from unittest.mock import AsyncMock, Mock

import astroplan
import astropy.units as u
import pytest
import pytest_mock
from astroplan import ObservingBlock, FixedTarget, Observer
from astropy.coordinates import SkyCoord

from pyobs.modules.robotic._taskscheduler import _TaskScheduler
from pyobs.utils.time import Time
from tests.modules.robotic.test_mastermind import TestTask
from tests.modules.robotic.test_scheduler import TestTaskSchedule


@pytest.mark.asyncio
async def test_prepare_schedule_invalid_twilight(observer: Observer) -> None:
    with pytest.raises(ValueError):
        _TaskScheduler(TestTaskSchedule(), observer, 24, 60, "invalid")


@pytest.mark.asyncio
async def test_prepare_schedule_astronomical_twilight(observer: Observer, schedule_blocks: List[ObservingBlock]) -> None:
    scheduler = _TaskScheduler(TestTaskSchedule(), observer, 24, 60, "astronomical")

    assert scheduler._scheduler.constraints[0].max_solar_altitude == -18 * u.deg


@pytest.mark.asyncio
async def test_prepare_schedule_nautical_twilight(observer: Observer, schedule_blocks: List[ObservingBlock]) -> None:
    scheduler = _TaskScheduler(TestTaskSchedule(), observer, 24, 60, "nautical")
    assert scheduler._scheduler.constraints[0].max_solar_altitude == -12 * u.deg


@pytest.mark.asyncio
async def test_prepare_schedule_no_blocks(observer: Observer) -> None:
    scheduler = _TaskScheduler(TestTaskSchedule(), observer, 24, 60, "nautical")

    with pytest.raises(ValueError):
        await scheduler._prepare_schedule()


@pytest.mark.asyncio
async def test_prepare_schedule_no_start(observer: Observer, schedule_blocks: List[ObservingBlock], mocker: pytest_mock.MockFixture) -> None:
    current_time = Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)

    scheduler = _TaskScheduler(TestTaskSchedule(), observer, 24, 60, "nautical")
    scheduler._blocks = schedule_blocks

    _, start, _ = await scheduler._prepare_schedule()

    assert start.to_datetime() == datetime.datetime(2024, 4, 1, 20, 1, 0)


@pytest.mark.asyncio
async def test_prepare_schedule_start(observer: Observer, schedule_blocks: List[ObservingBlock], mocker: pytest_mock.MockFixture) -> None:
    current_time = Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)

    scheduler = _TaskScheduler(TestTaskSchedule(), observer, 24, 60, "nautical")
    scheduler._blocks = schedule_blocks
    scheduler._schedule_start = Time(datetime.datetime(2024, 4, 1, 20, 1, 0))

    _, start, _ = await scheduler._prepare_schedule()

    assert start.to_datetime() == datetime.datetime(2024, 4, 1, 20, 1, 0)


@pytest.mark.asyncio
async def test_prepare_schedule_end(observer: Observer, schedule_blocks: List[ObservingBlock], mocker: pytest_mock.MockFixture) -> None:
    current_time = Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)

    scheduler = _TaskScheduler(TestTaskSchedule(), observer, 24, 60, "nautical")
    scheduler._blocks = schedule_blocks
    scheduler._schedule_start = Time(datetime.datetime(2024, 4, 1, 20, 1, 0))

    _, _, end = await scheduler._prepare_schedule()

    assert end.to_datetime() == datetime.datetime(2024, 4, 2, 20, 1, 0)


@pytest.mark.asyncio
async def test_prepare_schedule_block_filtering(observer: Observer, schedule_blocks: List[ObservingBlock], mocker: pytest_mock.MockFixture) -> None:
    current_time = Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)

    over_time = Time(datetime.datetime(2024, 4, 3, 20, 0, 0))
    in_time = Time(datetime.datetime(2024, 4, 2, 10, 0, 0))

    schedule_blocks[1].constraints.append(astroplan.TimeConstraint(min=over_time, max=over_time))
    schedule_blocks[2].constraints.append(astroplan.TimeConstraint(min=in_time, max=over_time))

    blocks = [
        schedule_blocks[0], schedule_blocks[1], schedule_blocks[2], schedule_blocks[3]
    ]

    task_scheduler = TestTaskSchedule()
    task_scheduler.get_schedule = AsyncMock(return_value={"0": TestTask()})  # type: ignore

    scheduler = _TaskScheduler(task_scheduler, observer, 24, 60, "nautical")
    scheduler._schedule_start = Time(datetime.datetime(2024, 4, 1, 20, 1, 0))
    scheduler._current_task_id = "0"
    scheduler._blocks = blocks

    res_blocks, _, _ = await scheduler._prepare_schedule()

    assert [block.configuration["request"]["id"] for block in res_blocks] == ["2", "3"]


def mock_schedule_process(blocks: List[ObservingBlock], start: Time, end: Time,
                          scheduled_blocks: multiprocessing.Queue) -> None:  # type: ignore
    scheduled_blocks.put(blocks)


@pytest.mark.asyncio
async def test_schedule_blocks(observer: Observer) -> None:

    scheduler = _TaskScheduler(TestTaskSchedule(), observer, 24, 60, "nautical")
    scheduler._schedule_process = mock_schedule_process  # type: ignore

    time = Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    block = ObservingBlock(
        FixedTarget(SkyCoord(0.0 * u.deg, 0.0 * u.deg, frame="icrs"), name=0), 10 * u.minute, 2000.0,
        configuration={"request": {"id": "0"}}
    )
    blocks = [block]
    scheduled_blocks = await scheduler._schedule_blocks(blocks, time, time)
    assert scheduled_blocks[0].configuration["request"]["id"] == block.configuration["request"]["id"]


@pytest.mark.asyncio
async def test_finish_schedule(observer: Observer) -> None:
    scheduler = _TaskScheduler(TestTaskSchedule(), observer, 24, 60, "nautical")
    scheduler._schedule.set_schedule = AsyncMock()  # type: ignore

    time = Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    block = ObservingBlock(
        FixedTarget(SkyCoord(0.0 * u.deg, 0.0 * u.deg, frame="icrs"), name=0), 10 * u.minute, 2000.0,
        configuration={"request": {"id": "0"}},
        constraints=[astroplan.TimeConstraint(min=time, max=time)]
    )
    block.start_time = time
    block.end_time = time
    blocks = [block]

    await scheduler._finish_schedule(blocks, time)
    scheduler._schedule.set_schedule.assert_called_with(blocks, time)


@pytest.mark.asyncio
async def test_convert_blocks_to_astroplan(observer: Observer) -> None:
    scheduler = _TaskScheduler(TestTaskSchedule(), observer, 24, 60, "nautical")
    time = Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    block = ObservingBlock(
        FixedTarget(SkyCoord(0.0 * u.deg, 0.0 * u.deg, frame="icrs"), name=0), 10 * u.minute, 2000.0,
        constraints=[astroplan.TimeConstraint(min=time, max=time)]
    )
    scheduler._blocks = [block]

    converted_blocks = await scheduler._convert_blocks_to_astroplan()

    assert converted_blocks[0].priority == 0
    assert converted_blocks[0].constraints[0].min.to_datetime() == datetime.datetime(2024, 4, 1, 20, 0, 30)
    assert converted_blocks[0].constraints[0].max.to_datetime() == datetime.datetime(2024, 4, 1, 19, 59, 30)


class MockSchedule:
    def __init__(self, blocks: List[ObservingBlock]) -> None:
        self.scheduled_blocks = blocks


@pytest.mark.asyncio
async def test_schedule_process(observer: Observer) -> None:
    scheduler = _TaskScheduler(TestTaskSchedule(), observer, 24, 60, "nautical")

    time = Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    block = ObservingBlock(
        FixedTarget(SkyCoord(0.0 * u.deg, 0.0 * u.deg, frame="icrs"), name=0), 10 * u.minute, 2000.0,
        constraints=[astroplan.TimeConstraint(min=time, max=time)]
    )
    blocks = [block]
    scheduler._scheduler = Mock(return_value=MockSchedule(blocks))

    queue = multiprocessing.Queue()  # type: ignore
    scheduler._schedule_process(blocks, time, time, queue)
    converted_blocks = queue.get()

    assert converted_blocks[0].priority == 2000.0
    assert converted_blocks[0].constraints[0].min.to_datetime() == datetime.datetime(2024, 4, 1, 20, 0)
    assert converted_blocks[0].constraints[0].max.to_datetime() == datetime.datetime(2024, 4, 1, 20, 0)
