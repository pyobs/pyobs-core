from __future__ import annotations
from typing import TYPE_CHECKING

from pyobs.robotic import Task

if TYPE_CHECKING:
    from pyobs.robotic import TaskRunner, TaskSchedule, TaskArchive
    from pyobs.robotic.scripts import Script


class TestTask(Task):
    async def can_run(self, scripts: dict[str, Script] | None = None) -> bool:
        return True

    @property
    def can_start_late(self) -> bool:
        return False

    async def run(
        self,
        task_runner: TaskRunner,
        task_schedule: TaskSchedule | None = None,
        task_archive: TaskArchive | None = None,
        scripts: dict[str, Script] | None = None,
    ) -> None:
        pass

    def is_finished(self) -> bool:
        return False
