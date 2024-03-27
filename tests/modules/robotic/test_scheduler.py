from typing import List, Optional, Dict
from unittest.mock import Mock, AsyncMock

import astropy.units as u
import pytest
from astroplan import ObservingBlock, FixedTarget
from astropy.coordinates import SkyCoord

from pyobs.modules.robotic import Scheduler
from pyobs.robotic import TaskArchive, TaskSchedule, Task
from pyobs.utils.time import Time


@pytest.fixture
def schedule_blocks() -> List[ObservingBlock]:
    blocks = [
        ObservingBlock(
            FixedTarget(SkyCoord(0.0 * u.deg, 0.0 * u.deg, frame="icrs"), name=str(i)), 10 * u.minute, 10
        )
        for i in range(10)
    ]

    return blocks


def test_compare_block_lists_with_overlap(schedule_blocks):
    old_blocks = schedule_blocks[:7]
    new_blocks = schedule_blocks[5:]

    removed, added = Scheduler._compare_block_lists(old_blocks, new_blocks)

    removed_names = [int(b.target.name) for b in removed]
    new_names = [int(b.target.name) for b in added]

    assert set(removed_names) == {0, 1, 2, 3, 4}
    assert set(new_names) == {7, 8, 9}


def test_compare_block_lists_without_overlap(schedule_blocks):
    old_blocks = schedule_blocks[:5]
    new_blocks = schedule_blocks[5:]

    removed, added = Scheduler._compare_block_lists(old_blocks, new_blocks)

    removed_names = [int(b.target.name) for b in removed]
    new_names = [int(b.target.name) for b in added]

    assert set(removed_names) == {0, 1, 2, 3, 4}
    assert set(new_names) == {5, 6, 7, 8, 9}


def test_compare_block_lists_identical(schedule_blocks):
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
async def test_worker_loop_not_changed():
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._need_update = False

    scheduler._task_archive.last_changed = AsyncMock(return_value=Time.now())
    scheduler._last_change = Time.now()

    await scheduler._worker_loop()

    assert scheduler._need_update is False


@pytest.mark.asyncio
async def test_worker_loop_no_changes(schedule_blocks):
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._task_archive.get_schedulable_blocks = AsyncMock(return_value=schedule_blocks)
    scheduler._blocks = schedule_blocks

    scheduler._need_update = False

    await scheduler._worker_loop()

    assert scheduler._need_update is False


@pytest.mark.asyncio
async def test_worker_loop_removed_current(schedule_blocks):
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._task_archive.get_schedulable_blocks = AsyncMock(return_value=schedule_blocks)
    scheduler._blocks = schedule_blocks
    scheduler._last_task_id = "0"

    scheduler._compare_block_lists = Mock(return_value=([schedule_blocks[0]], []))

    scheduler._need_update = False

    await scheduler._worker_loop()

    assert scheduler._need_update is False


@pytest.mark.asyncio
async def test_worker_loop_removed_not_in_schedule(schedule_blocks):
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._task_archive.get_schedulable_blocks = AsyncMock(return_value=schedule_blocks)
    scheduler._schedule.get_schedule = AsyncMock(return_value=[])
    scheduler._blocks = schedule_blocks

    scheduler._compare_block_lists = Mock(return_value=([schedule_blocks[0]], []))

    scheduler._need_update = False

    await scheduler._worker_loop()

    assert scheduler._need_update is False


@pytest.mark.asyncio
async def test_worker_loop_need_to_update(schedule_blocks):
    scheduler = Scheduler(TestTaskArchive(), TestTaskSchedule())
    scheduler._task_archive.get_schedulable_blocks = AsyncMock(return_value=schedule_blocks)
    scheduler._schedule.get_schedule = AsyncMock(return_value=[])
    scheduler._blocks = []

    scheduler._compare_block_lists = Mock(return_value=([], [schedule_blocks[0]]))

    scheduler._need_update = False

    await scheduler._worker_loop()

    assert scheduler._need_update is True
    assert scheduler._blocks == schedule_blocks
