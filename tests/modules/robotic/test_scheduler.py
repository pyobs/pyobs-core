from typing import List

import astropy.units as u
import pytest
from astroplan import ObservingBlock, FixedTarget
from astropy.coordinates import SkyCoord

from pyobs.modules.robotic import Scheduler


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
