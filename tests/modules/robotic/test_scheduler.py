from astroplan import ObservingBlock, FixedTarget
import astropy.units as u
from astropy.coordinates import SkyCoord

from pyobs.modules.robotic import Scheduler


def test_compare_block_lists():
    # create lists of blocks
    blocks = []
    for i in range(10):
        blocks.append(
            ObservingBlock(
                FixedTarget(SkyCoord(0.0 * u.deg, 0.0 * u.deg, frame="icrs"), name=str(i)), 10 * u.minute, 10
            )
        )

    # create two lists from these with some overlap
    blocks1 = blocks[:7]
    blocks2 = blocks[5:]

    # compare
    unique1, unique2 = Scheduler._compare_task_lists(blocks1, blocks2)

    # get names
    names1 = [int(b.target.name) for b in unique1]
    names2 = [int(b.target.name) for b in unique2]

    # names1 should contain 0, 1, 2, 3, 4
    assert set(names1) == {0, 1, 2, 3, 4}

    # names2 should contain 7, 8, 9
    assert set(names2) == {7, 8, 9}

    # create two lists from these with no overlap
    blocks1 = blocks[:5]
    blocks2 = blocks[5:]

    # compare
    unique1, unique2 = Scheduler._compare_task_lists(blocks1, blocks2)

    # get names
    names1 = [int(b.target.name) for b in unique1]
    names2 = [int(b.target.name) for b in unique2]

    # names1 should contain 0, 1, 2, 3, 4
    assert set(names1) == {0, 1, 2, 3, 4}

    # names2 should contain 5, 6, 7, 8, 9
    assert set(names2) == {5, 6, 7, 8, 9}

    # create two identical lists
    blocks1 = blocks
    blocks2 = blocks

    # compare
    unique1, unique2 = Scheduler._compare_task_lists(blocks1, blocks2)

    # get names
    names1 = [int(b.target.name) for b in unique1]
    names2 = [int(b.target.name) for b in unique2]

    # both lists should be empty
    assert len(names1) == 0
    assert len(names2) == 0
