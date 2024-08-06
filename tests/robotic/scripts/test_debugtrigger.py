import logging
import pytest

from pyobs.robotic.scripts.debugtrigger import DebugTriggerRunner


@pytest.mark.asyncio
async def test_trigger():
    runner = DebugTriggerRunner()
    await runner.run(None, None, None)
    assert runner.triggered is True
