from pyobs.modules.robotic import Scheduler
from pyobs.robotic import Task, TaskRunner, TaskSchedule, TaskArchive
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


def test_compare_block_lists() -> None:
    # create lists of tasks
    tasks: list[Task] = []
    for i in range(10):
        tasks.append(TestTask(i, str(i), 100))

    # create two lists from these with some overlap
    tasks1 = tasks[:7]
    tasks2 = tasks[5:]

    # compare
    unique1, unique2 = Scheduler._compare_task_lists(tasks1, tasks2)

    # names1 should contain 0, 1, 2, 3, 4
    assert set(unique1) == {0, 1, 2, 3, 4}

    # names2 should contain 7, 8, 9
    assert set(unique2) == {7, 8, 9}

    # create two lists from these with no overlap
    tasks1 = tasks[:5]
    tasks2 = tasks[5:]

    # compare
    unique1, unique2 = Scheduler._compare_task_lists(tasks1, tasks2)

    # names1 should contain 0, 1, 2, 3, 4
    assert set(unique1) == {0, 1, 2, 3, 4}

    # names2 should contain 5, 6, 7, 8, 9
    assert set(unique2) == {5, 6, 7, 8, 9}

    # create two identical lists
    tasks1 = tasks
    tasks2 = tasks

    # compare
    unique1, unique2 = Scheduler._compare_task_lists(tasks1, tasks2)

    # both lists should be empty
    assert len(unique1) == 0
    assert len(unique2) == 0
