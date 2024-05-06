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

