import datetime
from typing import List
from unittest.mock import Mock, AsyncMock

import pytest
import pytest_mock
from astroplan import ObservingBlock

import pyobs
from pyobs.modules.robotic._taskupdater import _TaskUpdater
from pyobs.utils.time import Time
from tests.modules.robotic.test_scheduler import TestTaskArchive, TestTaskSchedule


def test_compare_block_lists_with_overlap(schedule_blocks: List[ObservingBlock]) -> None:
    old_blocks = schedule_blocks[:7]
    new_blocks = schedule_blocks[5:]

    removed, added = _TaskUpdater._compare_block_lists(old_blocks, new_blocks)

    removed_names = [int(b.target.name) for b in removed]
    new_names = [int(b.target.name) for b in added]

    assert set(removed_names) == {0, 1, 2, 3, 4}
    assert set(new_names) == {7, 8, 9}


def test_compare_block_lists_without_overlap(schedule_blocks: List[ObservingBlock]) -> None:
    old_blocks = schedule_blocks[:5]
    new_blocks = schedule_blocks[5:]

    removed, added = _TaskUpdater._compare_block_lists(old_blocks, new_blocks)

    removed_names = [int(b.target.name) for b in removed]
    new_names = [int(b.target.name) for b in added]

    assert set(removed_names) == {0, 1, 2, 3, 4}
    assert set(new_names) == {5, 6, 7, 8, 9}


def test_compare_block_lists_identical(schedule_blocks: List[ObservingBlock]) -> None:
    old_blocks = schedule_blocks
    new_blocks = schedule_blocks

    removed, added = _TaskUpdater._compare_block_lists(old_blocks, new_blocks)

    removed_names = [int(b.target.name) for b in removed]
    new_names = [int(b.target.name) for b in added]

    assert len(removed_names) == 0
    assert len(new_names) == 0


@pytest.mark.asyncio
async def test_worker_loop_not_changed() -> None:
    scheduler = _TaskUpdater(TestTaskArchive(), TestTaskSchedule())
    scheduler._update_blocks = AsyncMock()  # type: ignore

    time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    scheduler._task_archive.last_changed = AsyncMock(return_value=time)  # type: ignore
    scheduler._last_change = time

    await scheduler.update()

    scheduler._update_blocks.assert_not_called()


@pytest.mark.asyncio
async def test_worker_loop_new_changes(mocker: pytest_mock.MockFixture) -> None:
    time = pyobs.utils.time.Time(datetime.datetime(2024, 4, 1, 20, 0, 0))
    mocker.patch("pyobs.utils.time.Time.now", return_value=time)
    scheduler = _TaskUpdater(TestTaskArchive(), TestTaskSchedule())
    scheduler._update_blocks = AsyncMock()  # type: ignore

    scheduler._task_archive.last_changed = AsyncMock(return_value=time)  # type: ignore
    scheduler._last_change = time - datetime.timedelta(minutes=1)  # type: ignore

    await scheduler.update()

    scheduler._update_blocks.assert_called_once()
    assert scheduler._last_change == time


@pytest.mark.asyncio
async def test_update_blocks_no_changes(schedule_blocks: List[ObservingBlock]) -> None:
    scheduler = _TaskUpdater(TestTaskArchive(), TestTaskSchedule())
    scheduler._task_archive.get_schedulable_blocks = AsyncMock(return_value=schedule_blocks)  # type: ignore
    scheduler._blocks = schedule_blocks

    assert await scheduler._update_blocks() is None


@pytest.mark.asyncio
async def test_update_blocks_removed_current(schedule_blocks: List[ObservingBlock]) -> None:
    scheduler = _TaskUpdater(TestTaskArchive(), TestTaskSchedule())

    scheduler._task_archive.get_schedulable_blocks = AsyncMock(return_value=schedule_blocks)  # type: ignore
    scheduler._blocks = schedule_blocks
    scheduler._last_task_id = "0"

    scheduler._compare_block_lists = Mock(return_value=([schedule_blocks[0]], []))  # type: ignore

    assert await scheduler._update_blocks() is None


@pytest.mark.asyncio
async def test_update_blocks_removed_not_in_schedule(schedule_blocks: List[ObservingBlock]) -> None:
    scheduler = _TaskUpdater(TestTaskArchive(), TestTaskSchedule())
    scheduler._task_archive.get_schedulable_blocks = AsyncMock(return_value=schedule_blocks)  # type: ignore
    scheduler._schedule.get_schedule = AsyncMock(return_value=[])  # type: ignore
    scheduler._blocks = schedule_blocks

    scheduler._compare_block_lists = Mock(return_value=([schedule_blocks[0]], []))  # type: ignore

    assert await scheduler._update_blocks() is None


@pytest.mark.asyncio
async def test_update_blocks_need_to_update(schedule_blocks: List[ObservingBlock]) -> None:
    scheduler = _TaskUpdater(TestTaskArchive(), TestTaskSchedule())

    scheduler._task_archive.get_schedulable_blocks = AsyncMock(return_value=schedule_blocks)  # type: ignore
    scheduler._schedule.get_schedule = AsyncMock(return_value=[])  # type: ignore
    scheduler._blocks = []

    scheduler._compare_block_lists = Mock(return_value=([], [schedule_blocks[0]]))  # type: ignore

    assert await scheduler._update_blocks() == schedule_blocks