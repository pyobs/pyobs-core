from unittest.mock import AsyncMock

import pyobs
from pyobs.background_task import BackgroundTask
from pyobs.object import Object


def test_add_background_task():
    obj = Object()
    test_function = AsyncMock()

    task = obj.add_background_task(test_function, False, False)

    assert task._func == test_function
    assert task._restart is False

    assert obj._background_tasks[0] == (task, False)


def test_perform_background_task_autostart(mocker):
    mocker.patch("pyobs.background_task.BackgroundTask.start")

    obj = Object()
    test_function = AsyncMock()

    obj.add_background_task(test_function, False, True)
    obj._perform_background_task_autostart()

    pyobs.background_task.BackgroundTask.start.assert_called_once()


def test_perform_background_task_no_autostart(mocker):
    mocker.patch("pyobs.background_task.BackgroundTask.start")

    obj = Object()
    test_function = AsyncMock()

    obj.add_background_task(test_function, False, False)
    obj._perform_background_task_autostart()

    pyobs.background_task.BackgroundTask.start.assert_not_called()


def test_stop_background_task(mocker):
    mocker.patch("pyobs.background_task.BackgroundTask.stop")

    obj = Object()
    test_function = AsyncMock()

    obj.add_background_task(test_function, False, False)
    obj._stop_background_tasks()

    pyobs.background_task.BackgroundTask.stop.assert_called_once()