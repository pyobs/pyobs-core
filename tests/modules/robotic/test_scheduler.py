import datetime
import multiprocessing
from typing import List, Optional, Dict, Any
from unittest.mock import Mock, AsyncMock

import astroplan
import astropy.units as u
import pytest
from astroplan import ObservingBlock, FixedTarget, Observer
from astropy.coordinates import SkyCoord

import pyobs
from pyobs.events import GoodWeatherEvent, TaskStartedEvent, TaskFinishedEvent, Event
from pyobs.modules.robotic import Scheduler
from pyobs.robotic import TaskArchive, TaskSchedule, Task
from pyobs.utils.time import Time
from tests.modules.robotic.test_mastermind import TestTask


@pytest.fixture
def schedule_blocks() -> List[ObservingBlock]:
    blocks = [
        ObservingBlock(
            FixedTarget(SkyCoord(0.0 * u.deg, 0.0 * u.deg, frame="icrs"), name=str(i)), 10 * u.minute, 10,
            constraints=[], configuration={"request": {"id": str(i)}}
        )
        for i in range(10)
    ]

    return blocks


def test_compare_block_lists_with_overlap(schedule_blocks) -> None:
    old_blocks = schedule_blocks[:7]
    new_blocks = schedule_blocks[5:]

    removed, added = Scheduler._compare_block_lists(old_blocks, new_blocks)

    removed_names = [int(b.target.name) for b in removed]
    new_names = [int(b.target.name) for b in added]

    assert set(removed_names) == {0, 1, 2, 3, 4}
    assert set(new_names) == {7, 8, 9}


def test_compare_block_lists_without_overlap(schedule_blocks) -> None:
    old_blocks = schedule_blocks[:5]
    new_blocks = schedule_blocks[5:]

    removed, added = Scheduler._compare_block_lists(old_blocks, new_blocks)

    removed_names = [int(b.target.name) for b in removed]
    new_names = [int(b.target.name) for b in added]

    assert set(removed_names) == {0, 1, 2, 3, 4}
    assert set(new_names) == {5, 6, 7, 8, 9}


def test_compare_block_lists_identical(schedule_blocks) -> None:
    old_blocks = schedule_blocks
    new_blocks = schedule_blocks

    removed, added = Scheduler._compare_block_lists(old_blocks, new_blocks)

    removed_names = [int(b.target.name) for b in removed]
    new_names = [int(b.target.name) for b in added]

    assert len(removed_names) == 0
    assert len(new_names) == 0


class TestTaskArchive(TaskArchive):

    async def last_changed(self) -> Optional[Time]:
        pass

    async def get_schedulable_blocks(self) -> List[ObservingBlock]:
        pass


class TestTaskSchedule(TaskSchedule):

    async def set_schedule(self, blocks: List[ObservingBlock], start_time: Time) -> None:
        pass

    async def last_scheduled(self) -> Optional[Time]:
        pass

    async def get_schedule(self) -> Dict[str, Task]:
        pass

    async def get_task(self, time: Time) -> Optional[Task]:
        pass


@pytest.mark.asyncio
async def test_worker_loop_not_changed() -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._update_blocks = AsyncMock()

    time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    scheduler._task_archive.last_changed = AsyncMock(return_value=time)  # type: ignore
    scheduler._last_change = time

    await scheduler._update_worker_loop()

    scheduler._update_blocks.assert_not_called()


@pytest.mark.asyncio
async def test_worker_loop_new_changes(mocker) -> None:
    time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    mocker.patch("pyobs.utils.time.Time.now", return_value=time)
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._update_blocks = AsyncMock()

    scheduler._task_archive.last_changed = AsyncMock(return_value=time)  # type: ignore
    scheduler._last_change = time - datetime.timedelta(minutes=1)

    await scheduler._update_worker_loop()

    scheduler._update_blocks.assert_called_once()
    assert scheduler._last_change == time


@pytest.mark.asyncio
async def test_update_blocks_no_changes(schedule_blocks) -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._scheduler_task.start = Mock()  # type: ignore
    scheduler._task_archive.get_schedulable_blocks = AsyncMock(return_value=schedule_blocks)  # type: ignore
    scheduler._blocks = schedule_blocks

    await scheduler._update_blocks()

    scheduler._scheduler_task.start.assert_not_called()


@pytest.mark.asyncio
async def test_update_blocks_removed_current(schedule_blocks) -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._scheduler_task.start = Mock()  # type: ignore

    scheduler._task_archive.get_schedulable_blocks = AsyncMock(return_value=schedule_blocks)  # type: ignore
    scheduler._blocks = schedule_blocks
    scheduler._last_task_id = "0"

    scheduler._compare_block_lists = Mock(return_value=([schedule_blocks[0]], []))  # type: ignore

    await scheduler._update_blocks()

    scheduler._scheduler_task.start.assert_not_called()


@pytest.mark.asyncio
async def test_update_blocks_removed_not_in_schedule(schedule_blocks)  -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._scheduler_task.start = Mock()  # type: ignore
    scheduler._task_archive.get_schedulable_blocks = AsyncMock(return_value=schedule_blocks)  # type: ignore
    scheduler._schedule.get_schedule = AsyncMock(return_value=[])  # type: ignore
    scheduler._blocks = schedule_blocks

    scheduler._compare_block_lists = Mock(return_value=([schedule_blocks[0]], []))  # type: ignore

    await scheduler._update_blocks()

    scheduler._scheduler_task.start.assert_not_called()


@pytest.mark.asyncio
async def test_update_blocks_need_to_update(schedule_blocks) -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._scheduler_task.start = Mock()  # type: ignore
    scheduler._task_archive.get_schedulable_blocks = AsyncMock(return_value=schedule_blocks)  # type: ignore
    scheduler._schedule.get_schedule = AsyncMock(return_value=[])  # type: ignore
    scheduler._blocks = []

    scheduler._compare_block_lists = Mock(return_value=([], [schedule_blocks[0]]))  # type: ignore

    await scheduler._update_blocks()

    scheduler._scheduler_task.start.assert_called_once()
    assert scheduler._blocks == schedule_blocks


@pytest.mark.asyncio
async def test_prepare_schedule_invalid_twilight() -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), twilight="invalid")

    with pytest.raises(ValueError):
        await scheduler._prepare_schedule()


@pytest.mark.asyncio
async def test_prepare_schedule_astronomical_twilight(schedule_blocks) -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), twilight="astronomical")
    scheduler._blocks = schedule_blocks

    _, _, _, constraints = await scheduler._prepare_schedule()

    assert constraints[0].max_solar_altitude == -18 * u.deg


@pytest.mark.asyncio
async def test_prepare_schedule_nautical_twilight(schedule_blocks) -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), twilight="nautical")
    scheduler._blocks = schedule_blocks

    _, _, _, constraints = await scheduler._prepare_schedule()

    assert constraints[0].max_solar_altitude == -12 * u.deg


@pytest.mark.asyncio
async def test_prepare_schedule_no_blocks() -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), twilight="nautical")

    with pytest.raises(ValueError):
        await scheduler._prepare_schedule()


@pytest.mark.asyncio
async def test_prepare_schedule_no_start(schedule_blocks, mocker) -> None:
    current_time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)

    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._blocks = schedule_blocks

    _, start, _, _ = await scheduler._prepare_schedule()

    assert start.to_datetime() == datetime.datetime(2024, 4, 1, 20, 1, 0)


@pytest.mark.asyncio
async def test_prepare_schedule_start(schedule_blocks, mocker) -> None:
    current_time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)

    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._blocks = schedule_blocks
    scheduler._schedule_start = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 1, 0))

    _, start, _, _ = await scheduler._prepare_schedule()

    assert start.to_datetime() == datetime.datetime(2024, 4, 1, 20, 1, 0)


@pytest.mark.asyncio
async def test_prepare_schedule_end(schedule_blocks, mocker) -> None:
    current_time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)

    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._blocks = schedule_blocks
    scheduler._schedule_start = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 1, 0))

    _, _, end, _ = await scheduler._prepare_schedule()

    assert end.to_datetime() == datetime.datetime(2024, 4, 2, 20, 1, 0)


@pytest.mark.asyncio
async def test_prepare_schedule_block_filtering(schedule_blocks, mocker) -> None:
    current_time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)

    over_time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 3, 20, 0, 0))
    in_time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 2, 10, 0, 0))

    schedule_blocks[1].constraints.append(astroplan.TimeConstraint(min=over_time, max=over_time))
    schedule_blocks[2].constraints.append(astroplan.TimeConstraint(min=in_time, max=over_time))

    blocks = [
        schedule_blocks[0], schedule_blocks[1], schedule_blocks[2], schedule_blocks[3]
    ]

    task_scheduler = TestTaskSchedule()
    task_scheduler.get_schedule = AsyncMock(return_value={"0": TestTask()})  # type: ignore

    scheduler = Scheduler(TestTaskArchive(), task_scheduler)
    scheduler._schedule_start = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 1, 0))
    scheduler._current_task_id = "0"
    scheduler._blocks = blocks

    res_blocks, _, _, _ = await scheduler._prepare_schedule()

    assert [block.configuration["request"]["id"] for block in res_blocks] == ["2", "3"]


def mock_schedule_process(blocks: List[ObservingBlock], start: Time, end: Time, constraints: List[Any],
                          scheduled_blocks: multiprocessing.Queue) -> None:  # type: ignore
    scheduled_blocks.put(blocks)


@pytest.mark.asyncio
async def test_schedule_blocks(observer) -> None:

    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), observer=observer)

    scheduler._schedule_process = mock_schedule_process  # type: ignore

    time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    block = ObservingBlock(
        FixedTarget(SkyCoord(0.0 * u.deg, 0.0 * u.deg, frame="icrs"), name=0), 10 * u.minute, 2000.0,
        configuration={"request": {"id": "0"}}
    )
    blocks = [block]
    scheduled_blocks = await scheduler._schedule_blocks(blocks, time, time, [])
    assert scheduled_blocks[0].configuration["request"]["id"] == block.configuration["request"]["id"]


@pytest.mark.asyncio
async def test_finish_schedule() -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._schedule.set_schedule = AsyncMock()  # type: ignore

    time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    block = ObservingBlock(
        FixedTarget(SkyCoord(0.0 * u.deg, 0.0 * u.deg, frame="icrs"), name=0), 10 * u.minute, 2000.0,
        configuration={"request": {"id": "0"}},
        constraints=[astroplan.TimeConstraint(min=time, max=time)]
    )
    block.start_time = time
    block.end_time = time
    blocks = [block]

    scheduler._need_update = False

    await scheduler._finish_schedule(blocks, time)
    scheduler._schedule.set_schedule.assert_called_with(blocks, time)


@pytest.mark.asyncio
async def test_on_task_started() -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), trigger_on_task_started=True)
    scheduler._scheduler_task.start = Mock()  # type: ignore
    time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    event = TaskStartedEvent(id=0, eta=time, name="")

    await scheduler._on_task_started(event, "")

    assert scheduler._current_task_id == 0
    assert scheduler._last_task_id == 0
    scheduler._scheduler_task.start.assert_called_once()
    assert scheduler._schedule_start == time


@pytest.mark.asyncio
async def test_on_task_started_wrong_event() -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), trigger_on_task_started=True)
    event = Event()

    assert await scheduler._on_task_started(event, "") is False


@pytest.mark.asyncio
async def test_on_task_finished(mocker) -> None:
    current_time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)

    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), trigger_on_task_finished=True)
    scheduler._scheduler_task.start = Mock()  # type: ignore
    event = TaskFinishedEvent(id=0, name="")

    await scheduler._on_task_finished(event, "")

    assert scheduler._current_task_id is None
    scheduler._scheduler_task.start.assert_called_once()

    assert scheduler._schedule_start == current_time


@pytest.mark.asyncio
async def test_on_task_finished_wrong_event() -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), trigger_on_task_started=True)
    event = Event()

    assert await scheduler._on_task_finished(event, "") is False


@pytest.mark.asyncio
async def test_on_good_weather() -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), trigger_on_task_started=True)
    scheduler._scheduler_task.start = Mock()  # type: ignore

    time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    event = GoodWeatherEvent(id=0, eta=time, name="")

    await scheduler._on_good_weather(event, "")

    scheduler._scheduler_task.start.assert_called_once()
    assert scheduler._schedule_start == time


@pytest.mark.asyncio
async def test_on_good_weather_not_weather_event() -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), trigger_on_task_started=True)
    event = Event()

    assert await scheduler._on_good_weather(event, "") is False


@pytest.mark.asyncio
async def test_convert_blocks_to_astroplan() -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    block = ObservingBlock(
        FixedTarget(SkyCoord(0.0 * u.deg, 0.0 * u.deg, frame="icrs"), name=0), 10 * u.minute, 2000.0,
        constraints=[astroplan.TimeConstraint(min=time, max=time)]
    )
    scheduler._blocks = [block]

    converted_blocks = await scheduler._convert_blocks_to_astroplan()

    assert converted_blocks[0].priority == 0
    assert converted_blocks[0].constraints[0].min.to_datetime() == datetime.datetime(2024, 4, 1, 20, 0, 30)
    assert converted_blocks[0].constraints[0].max.to_datetime() == datetime.datetime(2024, 4, 1, 19, 59, 30)
