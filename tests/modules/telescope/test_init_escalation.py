"""#1031/#1034: an init() that was aborted or refused on purpose must not escalate the telescope module to ERROR."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from pyobs.modules.module import Module
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import ModuleState
from tests.modules.telescope.test_dummyradectelescope import make_dummyradectelescope


def _make_failing(error: exc.PyobsError) -> Any:
    tel = make_dummyradectelescope()

    async def _init(**kwargs: Any) -> None:
        raise error

    tel._methods["init"] = (_init, tel._methods["init"][1], tel._methods["init"][2])
    tel._state = ModuleState.READY
    return tel


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error_type",
    [exc.InitAbortedError, exc.InitRefusedError],
)
async def test_expected_init_rejection_does_not_escalate(error_type: type[exc.PyobsError]) -> None:
    tel = _make_failing(error_type("Startup of telescope was interrupted."))
    for _ in range(4):
        with pytest.raises(error_type):
            await tel.execute("init", sender="t")
        await asyncio.sleep(0.01)
    assert tel._state == ModuleState.READY


@pytest.mark.asyncio
async def test_failed_init_still_escalates() -> None:
    tel = _make_failing(exc.InitError("PLC refused"))
    for _ in range(3):
        with pytest.raises(exc.InitError):
            await tel.execute("init", sender="t")
        await asyncio.sleep(0.01)
    assert tel._state == ModuleState.ERROR
    with pytest.raises(exc.ModuleError):
        await tel.execute("init", sender="t")


@pytest.mark.parametrize("error_type", [exc.InitAbortedError, exc.InitRefusedError])
def test_hierarchy(error_type: type[exc.PyobsError]) -> None:
    assert not issubclass(error_type, exc.MotionError)
    assert not issubclass(error_type, exc.InitError)
    assert not issubclass(error_type, exc.AbortedError)


@pytest.mark.asyncio
async def test_remote_expected_init_rejection_only_triggers_explicit_handlers() -> None:
    for error_type in (exc.InitAbortedError, exc.InitRefusedError):
        assert not Module._counts_as_remote_error(error_type("rejected", remote_module="telescope"))
    assert Module._counts_as_remote_error(exc.InitError("x", remote_module="telescope"))
