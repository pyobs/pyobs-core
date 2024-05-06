import datetime
from typing import List, Optional, Dict
from unittest.mock import Mock, AsyncMock

import pytest
import pytest_mock
from astroplan import ObservingBlock

import pyobs
from pyobs.events import GoodWeatherEvent, TaskStartedEvent, TaskFinishedEvent, Event
from pyobs.modules.robotic import Scheduler
from pyobs.robotic import TaskArchive, TaskSchedule, Task
from pyobs.utils.time import Time


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
async def test_update_worker_loop_no_update() -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), trigger_on_task_started=True)
    scheduler._task_updater.update = AsyncMock(return_value=None)  # type: ignore
    scheduler._scheduler_task.start = Mock()  # type: ignore

    await scheduler._update_worker_loop()

    scheduler._scheduler_task.start.assert_not_called()


@pytest.mark.asyncio
async def test_update_worker_loop_with_update() -> None:
    blocks: List[ObservingBlock] = []
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), trigger_on_task_started=True)
    scheduler._task_updater.update = AsyncMock(return_value=blocks)  # type: ignore
    scheduler._scheduler_task.start = Mock()  # type: ignore

    await scheduler._update_worker_loop()

    assert scheduler._task_scheduler._blocks == blocks
    scheduler._scheduler_task.start.assert_called_once()


@pytest.mark.asyncio
async def test_on_task_started() -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), trigger_on_task_started=True)
    scheduler._scheduler_task.start = Mock()  # type: ignore

    time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    event = TaskStartedEvent(id=0, eta=time, name="")

    await scheduler._on_task_started(event, "")

    assert scheduler._task_scheduler._current_task_id == 0  # type: ignore
    assert scheduler._task_updater._current_task_id == 0  # type: ignore
    assert scheduler._task_updater._last_task_id == 0  # type: ignore

    scheduler._scheduler_task.start.assert_called_once()
    assert scheduler._schedule_start == time


@pytest.mark.asyncio
async def test_on_task_started_wrong_event() -> None:
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), trigger_on_task_started=True)
    event = Event()

    assert await scheduler._on_task_started(event, "") is False


@pytest.mark.asyncio
async def test_on_task_finished(mocker: pytest_mock.MockFixture) -> None:
    current_time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    mocker.patch("pyobs.utils.time.Time.now", return_value=current_time)

    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule(), trigger_on_task_finished=True)
    scheduler._scheduler_task.start = Mock()  # type: ignore
    event = TaskFinishedEvent(id=0, name="")

    await scheduler._on_task_finished(event, "")

    assert scheduler._task_updater._current_task_id is None
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
