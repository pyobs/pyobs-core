import json
import json
import logging
from typing import List, Tuple, Optional

from astroplan import ObservingBlock

from pyobs.robotic import TaskArchive, TaskSchedule
from pyobs.utils.time import Time

log = logging.getLogger(__name__)


class _TaskUpdater:
    def __init__(self, task_archive: TaskArchive, task_schedule: TaskSchedule):
        self._task_archive = task_archive
        self._schedule = task_schedule

        self._blocks: List[ObservingBlock] = []

        self._current_task_id: Optional[str] = None
        self._last_task_id: Optional[str] = None

        self._last_change: Optional[Time] = None

    def set_current_task_id(self, task_id: Optional[str]) -> None:
        self._current_task_id = task_id

    def set_last_task_id(self, task_id: str) -> None:
        self._last_task_id = task_id

    async def update(self) -> Optional[List[ObservingBlock]]:
        # got new time of last change?
        t = await self._task_archive.last_changed()
        if self._last_change is None or self._last_change < t:
            blocks = await self._update_blocks()

            self._last_change = Time.now()
            return blocks

        return None

    async def _update_blocks(self) -> Optional[List[ObservingBlock]]:
        # get schedulable blocks and sort them
        log.info("Found update in schedulable block, downloading them...")
        blocks = sorted(
            await self._task_archive.get_schedulable_blocks(),
            key=lambda x: json.dumps(x.configuration, sort_keys=True),
        )
        log.info("Downloaded %d schedulable block(s).", len(blocks))

        # compare new and old lists
        removed, added = self._compare_block_lists(self._blocks, blocks)

        # store blocks
        self._blocks = blocks


        # schedule update
        if await self._need_update(removed, added):
            log.info("Triggering scheduler run...")
            return blocks
            #self._scheduler_task.stop()  # Stop current run
            #self._scheduler_task.start()

        return None

    async def _need_update(self, removed: List[ObservingBlock], added: List[ObservingBlock]) -> bool:
        if len(removed) == 0 and len(added) == 0:
            # no need to re-schedule
            log.info("No change in list of blocks detected.")
            return False

        # has only the current block been removed?
        log.info("Removed: %d, added: %d", len(removed), len(added))
        if len(removed) == 1:
            log.info(
                "Found 1 removed block with ID %d. Last task ID was %s, current is %s.",
                removed[0].target.name,
                str(self._last_task_id),
                str(self._current_task_id),
            )
        if len(removed) == 1 and len(added) == 0 and removed[0].target.name == self._last_task_id:
            # no need to re-schedule
            log.info("Only one removed block detected, which is the one currently running.")
            return False

        # check, if one of the removed blocks was actually in schedule
        if len(removed) > 0:
            schedule = await self._schedule.get_schedule()
            removed_from_schedule = [r for r in removed if r in schedule]
            if len(removed_from_schedule) == 0:
                log.info(f"Found {len(removed)} blocks, but none of them was scheduled.")
                return False

        return True

    @staticmethod
    def _compare_block_lists(
            blocks1: List[ObservingBlock], blocks2: List[ObservingBlock]
    ) -> Tuple[List[ObservingBlock], List[ObservingBlock]]:
        """Compares two lists of ObservingBlocks and returns two lists, containing those that are missing in list 1
        and list 2, respectively.

        Args:
            blocks1: First list of blocks.
            blocks2: Second list of blocks.

        Returns:
            (tuple): Tuple containing:
                unique1:  Blocks that exist in blocks1, but not in blocks2.
                unique2:  Blocks that exist in blocks2, but not in blocks1.
        """

        # get dictionaries with block names
        names1 = {b.target.name: b for b in blocks1}
        names2 = {b.target.name: b for b in blocks2}

        # find elements in names1 that are missing in names2 and vice versa
        additional1 = set(names1.keys()).difference(names2.keys())
        additional2 = set(names2.keys()).difference(names1.keys())

        # get blocks for names and return them
        unique1 = [names1[n] for n in additional1]
        unique2 = [names2[n] for n in additional2]
        return unique1, unique2