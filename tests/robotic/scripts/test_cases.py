"""
import pytest

from pyobs.robotic.scripts.cases import CasesRunner
from pyobs.robotic.scripts.debugtrigger import DebugTriggerRunner


@pytest.mark.asyncio
async def test_int_cases():
    cases = {1: DebugTriggerRunner(), 2: DebugTriggerRunner(), 10: DebugTriggerRunner()}
    cr = CasesRunner(expression="10", cases=cases)
    await cr.run(None, None, None)
    assert cases[1].triggered is False
    assert cases[2].triggered is False
    assert cases[10].triggered is True


@pytest.mark.asyncio
async def test_float_cases():
    cases = {3.14: DebugTriggerRunner(), 42.0: DebugTriggerRunner(), 2.7: DebugTriggerRunner()}
    cr = CasesRunner(expression="3.14", cases=cases)
    await cr.run(None, None, None)
    assert cases[3.14].triggered is True
    assert cases[42.0].triggered is False
    assert cases[2.7].triggered is False


@pytest.mark.asyncio
async def test_else():
    cases = {
        "1": DebugTriggerRunner(),
        "2": DebugTriggerRunner(),
        "3": DebugTriggerRunner(),
        "else": DebugTriggerRunner(),
    }
    cr = CasesRunner(expression="4", cases=cases)
    await cr.run(None, None, None)
    assert cases["1"].triggered is False
    assert cases["2"].triggered is False
    assert cases["3"].triggered is False
    assert cases["else"].triggered is True


@pytest.mark.asyncio
async def test_config():
    cases = {
        1: DebugTriggerRunner(),
        2: DebugTriggerRunner(),
        3: DebugTriggerRunner(),
        "else": DebugTriggerRunner(),
    }
    cr = CasesRunner(expression="config['abc']", cases=cases, configuration={"abc": 2})
    await cr.run(None, None, None)
    assert cases[1].triggered is False
    assert cases[2].triggered is True
    assert cases[3].triggered is False
    assert cases["else"].triggered is False
"""
