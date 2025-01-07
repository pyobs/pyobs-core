import asyncio
import logging
from datetime import timedelta
from typing import Optional, Dict, List, Any, Tuple
from unittest.mock import AsyncMock, Mock

import pytest
from astroplan import ObservingBlock

import pyobs
from pyobs.events import TaskStartedEvent, TaskFinishedEvent
from pyobs.modules.robotic import Mastermind
from pyobs.robotic import TaskSchedule, TaskRunner, Task, TaskArchive
from pyobs.robotic.scripts import Script
from pyobs.utils.time import Time


class TestTaskScheduler(TaskSchedule):
    async def set_schedule(self, blocks: List[ObservingBlock], start_time: Time) -> None:
        pass

    async def last_scheduled(self) -> Optional[Time]:
        pass

    async def get_schedule(self) -> Dict[str, Task]:
        pass

    async def get_task(self, time: Time) -> Optional[Task]:
        pass


class TestTask(Task):
    def __init__(self, start: Time = None, can_start_late: bool = False, **kwargs: Any):
        super().__init__(**kwargs)

        if start is None:
            self._start = Time.now()
        else:
            self._start = start

        self._can_start_late = can_start_late

    @property
    def id(self) -> Any:
        return 0

    @property
    def name(self) -> str:
        return "Task"

    @property
    def duration(self) -> float:
        return 0

    @property
    def start(self) -> Time:
        return self._start

    @property
    def end(self) -> Time:
        return self._start

    async def can_run(self, scripts: Optional[Dict[str, Script]] = None) -> bool:
        pass

    @property
    def can_start_late(self) -> bool:
        return self._can_start_late

    async def run(self, task_runner: TaskRunner, task_schedule: Optional[TaskSchedule] = None,
                  task_archive: Optional[TaskArchive] = None, scripts: Optional[Dict[str, Script]] = None) -> None:
        pass

    def is_finished(self) -> bool:
        pass

    def get_fits_headers(self, namespaces: Optional[List[str]] = None) -> Dict[str, Tuple[Any, str]]:
        return {"TASK-HDR": (0, "")}


@pytest.mark.asyncio
async def test_open(mocker):
    mocker.patch("pyobs.modules.Module.open")
    master = Mastermind(TestTaskScheduler(), TaskRunner())

    master.comm.register_event = AsyncMock()

    await master.open()

    pyobs.modules.Module.open.assert_called_once()
    assert master.comm.register_event.call_args_list[0][0][0] == TaskStartedEvent
    assert master.comm.register_event.call_args_list[1][0][0] == TaskFinishedEvent


@pytest.mark.asyncio
async def test_start():
    master = Mastermind(TestTaskScheduler(), TaskRunner())
    master._mastermind_loop.start = Mock()
    await master.start()

    master._mastermind_loop.start.assert_called_once()


@pytest.mark.asyncio
async def test_stop():
    master = Mastermind(TestTaskScheduler(), TaskRunner())
    master._mastermind_loop.stop = Mock()
    await master.stop()

    master._mastermind_loop.stop.assert_called_once()


@pytest.mark.asyncio
async def test_is_running():
    master = Mastermind(TestTaskScheduler(), TaskRunner())
    master._mastermind_loop.is_running = Mock(return_value=True)
    assert await master.is_running() is True


@pytest.mark.asyncio
async def test_loop_not_task(mocker):
    mocker.patch("asyncio.sleep")
    scheduler = TestTaskScheduler()
    scheduler.get_task = AsyncMock(return_value=None)
    master = Mastermind(scheduler, TaskRunner())

    await master._loop()
    asyncio.sleep.assert_called_once_with(10)


@pytest.mark.asyncio
async def test_loop_not_runnable_task(mocker):
    mocker.patch("asyncio.sleep")
    scheduler = TestTaskScheduler()
    scheduler.get_task = AsyncMock(return_value=TestTask())

    runner = TaskRunner()
    runner.can_run = AsyncMock(return_value=False)

    master = Mastermind(scheduler, runner)

    await master._loop()
    asyncio.sleep.assert_called_once_with(10)


@pytest.mark.asyncio
async def test_loop_late_start(mocker, caplog):
    mocker.patch("asyncio.sleep")
    task = TestTask(Time.now() - timedelta(seconds=400), False)

    scheduler = TestTaskScheduler()
    scheduler.get_task = AsyncMock(return_value=task)

    runner = TaskRunner()
    runner.can_run = AsyncMock(return_value=True)

    master = Mastermind(scheduler, runner)

    with caplog.at_level(logging.WARNING):
        await master._loop()
        await master._loop()

    assert caplog.messages[0] == "Time since start of window (400.0) too long (>300.0), skipping task..."

    assert len(caplog.messages) == 1    # Test that only the first task throws error msg

    asyncio.sleep.assert_called_with(10)


@pytest.mark.asyncio
async def test_loop_valid(mocker):
    mocker.patch("asyncio.sleep")
    task = TestTask(can_start_late=False)

    scheduler = TestTaskScheduler()
    scheduler.get_task = AsyncMock(return_value=task)

    runner = TaskRunner()
    runner.can_run = AsyncMock(return_value=True)
    runner.run_task = AsyncMock()

    master = Mastermind(scheduler, runner)

    await master._loop()

    asyncio.sleep.assert_not_called()
    runner.run_task.assert_awaited_with(task, task_schedule=scheduler)

    assert master._task is None


@pytest.mark.asyncio
async def test_loop_failed_task(mocker, caplog):
    mocker.patch("asyncio.sleep")
    task = TestTask(can_start_late=False)

    scheduler = TestTaskScheduler()
    scheduler.get_task = AsyncMock(return_value=task)

    runner = TaskRunner()
    runner.can_run = AsyncMock(return_value=True)
    runner.run_task = AsyncMock(side_effect=Exception(""))

    master = Mastermind(scheduler, runner)

    with caplog.at_level(logging.WARNING):
        await master._loop()

    asyncio.sleep.assert_not_called()

    assert caplog.messages[0] == "Task Task failed."
    assert master._task is None


@pytest.mark.asyncio
async def test_get_fits_header_before_without_task():
    master = Mastermind(TestTaskScheduler(), TaskRunner())

    header = await master.get_fits_header_before()

    assert header == {}


@pytest.mark.asyncio
async def test_get_fits_header_before_with_task():
    master = Mastermind(TestTaskScheduler(), TaskRunner())

    master._task = TestTask()

    header = await master.get_fits_header_before()

    assert header["TASK"] == ("Task", "Name of task")
    assert header["REQNUM"] == ("0", "Unique ID of task")
    assert header["TASK-HDR"] == (0, "")
