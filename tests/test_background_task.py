import asyncio
import logging
from unittest.mock import AsyncMock, Mock

import pytest
import pyobs.utils.exceptions as exc
from pyobs.background_task import BackgroundTask


@pytest.mark.asyncio
async def test_callback_canceled(caplog):
    test_function = AsyncMock()
    task = asyncio.create_task(test_function())
    task.exception = Mock(side_effect=asyncio.CancelledError())

    bg_task = BackgroundTask(test_function, False)
    bg_task._task = task

    with caplog.at_level(logging.ERROR):
        bg_task._callback_function()

    assert len(caplog.messages) == 0


@pytest.mark.asyncio
async def test_callback_exception(caplog):
    test_function = AsyncMock()
    test_function.__name__ = "test_function"

    task = asyncio.create_task(test_function())
    task.exception = Mock(return_value=Exception("TestError"))

    bg_task = BackgroundTask(test_function, False)
    bg_task._task = task

    with caplog.at_level(logging.ERROR):
        bg_task._callback_function()

    assert caplog.messages[0] == "Exception in task test_function."
    assert caplog.messages[1] == "Background task for test_function has died, quitting..."


@pytest.mark.asyncio
async def test_callback_pyobs_error():
    test_function = AsyncMock()
    test_function.__name__ = "test_function"

    task = asyncio.create_task(test_function())
    task.exception = Mock(return_value=exc.SevereError(exc.ImageError("TestError")))

    bg_task = BackgroundTask(test_function, False)
    bg_task._task = task

    with pytest.raises(exc.SevereError):
        bg_task._callback_function()


@pytest.mark.asyncio
async def test_callback_restart(caplog):
    test_function = AsyncMock()
    test_function.__name__ = "test_function"

    task = asyncio.create_task(test_function())
    task.exception = Mock(return_value=None)

    bg_task = BackgroundTask(test_function, True)
    bg_task._task = task

    bg_task.start = Mock()

    with caplog.at_level(logging.ERROR):
        bg_task._callback_function()

    assert caplog.messages[0] == "Background task for test_function has died, restarting..."
    bg_task.start.assert_called_once()

