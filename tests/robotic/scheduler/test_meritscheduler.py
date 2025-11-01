import pytest
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.robotic import Task, TaskRunner, TaskSchedule, TaskArchive
from pyobs.robotic.scheduler import DataProvider
from pyobs.robotic.scheduler.merits import ConstantMerit
from pyobs.robotic.scheduler.meritscheduler import find_next_best_task
from pyobs.robotic.scripts import Script
from pyobs.utils.time import Time


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


@pytest.mark.asyncio
async def test_next_best_task() -> None:
    observer = Observer(location=EarthLocation.of_site("SAAO"))
    data = DataProvider(observer)
    tasks: list[Task] = [
        TestTask(1, "1", 100, merits=[ConstantMerit(10)]),
        TestTask(1, "1", 100, merits=[ConstantMerit(5)]),
    ]
    best = await find_next_best_task(tasks, Time.now(), data)

    assert best.task == tasks[0]
