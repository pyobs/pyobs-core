import asyncio
import logging

import pytest

from pyobs.modules.test import StandAlone


def test_default():
    module = StandAlone()
    assert module._message == "Hello world"
    assert module._interval == 10


@pytest.mark.asyncio
async def test_loop(mocker, caplog):
    mocker.patch("asyncio.sleep", return_value=None)
    module = StandAlone("Testmessage", 3)

    with caplog.at_level(logging.INFO):
        await module._loop()

    assert caplog.messages[0] == "Testmessage"
    asyncio.sleep.assert_called_once_with(3)


@pytest.mark.asyncio
async def test_background_task():
    module = StandAlone()
    assert module._message_func in module._background_tasks
